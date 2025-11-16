"""
Recommendation Service
Handles ML recommendation creation, validation, and approval workflow
"""

import logging
import os
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Service to manage ML recommendations and approval workflow

    Three Safety Gates:
    1. Operator Approval (this service)
    2. Range Validation (this service)
    3. PLC Logic Validation (in PLC itself)
    """

    def __init__(self):
        self.db_host = os.getenv("POSTGRES_HOST", "localhost")
        self.db_port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.db_name = os.getenv("POSTGRES_DB", "context_edge")
        self.db_user = os.getenv("POSTGRES_USER", "context_user")
        self.db_password = os.getenv("POSTGRES_PASSWORD", "context_pass")

        # Default expiration time for recommendations (minutes)
        self.default_expiration_minutes = int(os.getenv("REC_EXPIRATION_MINUTES", "10"))

    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password
        )

    async def create_recommendation(
        self,
        device_id: str,
        recommendation: Dict[str, Any],
        ldo_id: Optional[str] = None
    ) -> str:
        """
        Create ML recommendation and validate against safety limits

        Args:
            device_id: Edge device ID
            recommendation: ML recommendation dict
            ldo_id: Optional LDO ID that generated this recommendation

        Returns:
            Recommendation ID
        """
        logger.info(f"📋 Creating recommendation for device: {device_id}")

        # Generate recommendation ID
        timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S%f")
        rec_id = f"REC-{timestamp_str}"

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Get safety limits for this parameter
            cur.execute("""
                SELECT min_value, max_value, max_rate_of_change, requires_approval
                FROM safety_limits
                WHERE device_id = %s
                  AND parameter_name = %s
                  AND enabled = true
            """, (device_id, recommendation["target_parameter"]))

            limits = cur.fetchone()

            if limits:
                min_val, max_val, max_change, requires_approval = limits

                # Validate against limits
                is_within_limits = (
                    min_val <= recommendation["recommended_value"] <= max_val
                )

                if not is_within_limits:
                    logger.warning(f"⚠️  Recommendation outside safe limits: {recommendation['recommended_value']} not in [{min_val}, {max_val}]")

            else:
                # No limits configured - allow but require approval
                logger.warning(f"⚠️  No safety limits configured for {device_id}/{recommendation['target_parameter']}")
                min_val = None
                max_val = None
                max_change = None
                is_within_limits = True
                requires_approval = True

            # Calculate expiration time
            expires_at = datetime.now() + timedelta(minutes=self.default_expiration_minutes)

            # Determine protocol adapter and register
            protocol_adapter, plc_register = self._get_adapter_config(
                device_id,
                recommendation["target_parameter"]
            )

            # Insert recommendation
            cur.execute("""
                INSERT INTO ml_recommendations (
                    recommendation_id, device_id, ldo_id,
                    action_type, target_parameter,
                    current_value, recommended_value, unit,
                    model_version, confidence, reasoning,
                    min_safe_value, max_safe_value, max_rate_of_change,
                    is_within_limits, status, priority,
                    protocol_adapter, plc_register, expires_at
                ) VALUES (
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s
                )
            """, (
                rec_id, device_id, ldo_id,
                recommendation["action_type"], recommendation["target_parameter"],
                recommendation.get("current_value"), recommendation["recommended_value"],
                recommendation.get("unit", ""),
                recommendation.get("model_version", "unknown"),
                recommendation.get("confidence", 0.0),
                recommendation.get("reasoning", ""),
                min_val, max_val, max_change,
                is_within_limits, "pending", recommendation.get("priority", 2),
                protocol_adapter, plc_register, expires_at
            ))

            # Audit log - creation
            cur.execute("""
                INSERT INTO ml_action_audit (recommendation_id, action, performed_by, details)
                VALUES (%s, %s, %s, %s)
            """, (rec_id, "created", "system", Json(recommendation)))

            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"✅ Recommendation created: {rec_id} (expires in {self.default_expiration_minutes} min)")
            return rec_id

        except Exception as e:
            logger.error(f"❌ Error creating recommendation: {e}", exc_info=True)
            raise

    async def get_pending_recommendations(
        self,
        device_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all pending recommendations (optionally filtered by device)

        Args:
            device_id: Optional device filter

        Returns:
            List of pending recommendations
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            if device_id:
                cur.execute("""
                    SELECT *, EXTRACT(EPOCH FROM (NOW() - created_at))/60 AS age_minutes
                    FROM ml_recommendations
                    WHERE status = 'pending'
                      AND device_id = %s
                      AND (expires_at IS NULL OR expires_at > NOW())
                    ORDER BY priority ASC, created_at ASC
                """, (device_id,))
            else:
                cur.execute("""
                    SELECT *, EXTRACT(EPOCH FROM (NOW() - created_at))/60 AS age_minutes
                    FROM ml_recommendations
                    WHERE status = 'pending'
                      AND (expires_at IS NULL OR expires_at > NOW())
                    ORDER BY priority ASC, created_at ASC
                """)

            recommendations = cur.fetchall()
            cur.close()
            conn.close()

            return [dict(rec) for rec in recommendations]

        except Exception as e:
            logger.error(f"❌ Error fetching recommendations: {e}", exc_info=True)
            return []

    async def approve_recommendation(
        self,
        rec_id: str,
        operator: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Operator approves recommendation (Safety Gate 1)

        Args:
            rec_id: Recommendation ID
            operator: Operator username/ID
            notes: Optional operator notes

        Returns:
            Approval result
        """
        logger.info(f"✅ Approving recommendation: {rec_id} by {operator}")

        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Get recommendation
            cur.execute("""
                SELECT * FROM ml_recommendations
                WHERE recommendation_id = %s
            """, (rec_id,))

            rec = cur.fetchone()

            if not rec:
                return {"success": False, "error": "Recommendation not found"}

            if rec["status"] != "pending":
                return {"success": False, "error": f"Recommendation already {rec['status']}"}

            # Check if expired
            if rec["expires_at"] and rec["expires_at"] < datetime.now():
                return {"success": False, "error": "Recommendation expired"}

            # Check if within safety limits (Safety Gate 2)
            if not rec["is_within_limits"]:
                return {"success": False, "error": "Recommendation outside safe limits"}

            # Update status to approved
            cur.execute("""
                UPDATE ml_recommendations
                SET status = 'approved',
                    approved_by = %s,
                    approved_at = NOW(),
                    operator_notes = %s,
                    updated_at = NOW()
                WHERE recommendation_id = %s
            """, (operator, notes, rec_id))

            # Audit log - approval
            cur.execute("""
                INSERT INTO ml_action_audit (recommendation_id, action, performed_by, details)
                VALUES (%s, %s, %s, %s)
            """, (rec_id, "approved", operator, Json({"notes": notes})))

            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"✅ Recommendation approved: {rec_id}")
            return {"success": True, "rec_id": rec_id, "status": "approved"}

        except Exception as e:
            logger.error(f"❌ Error approving recommendation: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def reject_recommendation(
        self,
        rec_id: str,
        operator: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Operator rejects recommendation

        Args:
            rec_id: Recommendation ID
            operator: Operator username/ID
            reason: Rejection reason

        Returns:
            Rejection result
        """
        logger.info(f"✗ Rejecting recommendation: {rec_id} by {operator}")

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Update status to rejected
            cur.execute("""
                UPDATE ml_recommendations
                SET status = 'rejected',
                    approved_by = %s,
                    approved_at = NOW(),
                    rejection_reason = %s,
                    updated_at = NOW()
                WHERE recommendation_id = %s
                  AND status = 'pending'
            """, (operator, reason, rec_id))

            # Audit log - rejection
            cur.execute("""
                INSERT INTO ml_action_audit (recommendation_id, action, performed_by, details)
                VALUES (%s, %s, %s, %s)
            """, (rec_id, "rejected", operator, Json({"reason": reason})))

            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"✅ Recommendation rejected: {rec_id}")
            return {"success": True, "rec_id": rec_id, "status": "rejected"}

        except Exception as e:
            logger.error(f"❌ Error rejecting recommendation: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def mark_executed(
        self,
        rec_id: str,
        execution_status: str,
        plc_response: Optional[str] = None
    ) -> None:
        """
        Mark recommendation as executed (or failed)

        Args:
            rec_id: Recommendation ID
            execution_status: 'success', 'failed', or 'plc_rejected'
            plc_response: Optional PLC response message
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE ml_recommendations
                SET status = 'executed',
                    execution_status = %s,
                    executed_at = NOW(),
                    plc_response = %s,
                    updated_at = NOW()
                WHERE recommendation_id = %s
            """, (execution_status, plc_response, rec_id))

            # Audit log - execution
            cur.execute("""
                INSERT INTO ml_action_audit (recommendation_id, action, performed_by, details)
                VALUES (%s, %s, %s, %s)
            """, (rec_id, "executed", "system", Json({"status": execution_status, "response": plc_response})))

            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"✅ Recommendation executed: {rec_id} (status: {execution_status})")

        except Exception as e:
            logger.error(f"❌ Error marking execution: {e}", exc_info=True)

    async def expire_old_recommendations(self) -> int:
        """
        Expire old recommendations that timed out

        Returns:
            Number of expired recommendations
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()

            cur.execute("SELECT expire_old_recommendations()")
            expired_count = cur.fetchone()[0]

            conn.commit()
            cur.close()
            conn.close()

            if expired_count > 0:
                logger.info(f"⏱️  Expired {expired_count} old recommendations")

            return expired_count

        except Exception as e:
            logger.error(f"❌ Error expiring recommendations: {e}", exc_info=True)
            return 0

    def _get_adapter_config(
        self,
        device_id: str,
        parameter: str
    ) -> tuple[str, str]:
        """
        Get protocol adapter and register for a device parameter

        Args:
            device_id: Edge device ID
            parameter: Parameter name (e.g., 'temperature')

        Returns:
            (adapter_name, register_address)
        """
        # TODO: Load from database configuration
        # For now, use defaults based on parameter name

        adapter_mapping = {
            "temperature": ("modbus", "40001"),
            "rpm": ("modbus", "40002"),
            "pressure": ("modbus", "40003"),
            "flow_rate": ("modbus", "40004")
        }

        return adapter_mapping.get(parameter, ("modbus", "40000"))

    async def get_safety_limits(
        self,
        device_id: str,
        parameter: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get safety limits for a device parameter

        Args:
            device_id: Edge device ID
            parameter: Parameter name

        Returns:
            Safety limits dict or None
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT * FROM safety_limits
                WHERE device_id = %s
                  AND parameter_name = %s
                  AND enabled = true
            """, (device_id, parameter))

            limits = cur.fetchone()
            cur.close()
            conn.close()

            return dict(limits) if limits else None

        except Exception as e:
            logger.error(f"❌ Error fetching safety limits: {e}", exc_info=True)
            return None
