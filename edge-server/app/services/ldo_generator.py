"""
LDO Generator Service
Creates Labeled Data Objects and stores them in PostgreSQL
"""

import logging
import os
import psycopg2
from psycopg2.extras import Json
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LDOGeneratorService:
    """Service to generate and store Labeled Data Objects"""

    def __init__(self):
        self.db_host = os.getenv("POSTGRES_HOST", "localhost")
        self.db_port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.db_name = os.getenv("POSTGRES_DB", "context_edge")
        self.db_user = os.getenv("POSTGRES_USER", "context_user")
        self.db_password = os.getenv("POSTGRES_PASSWORD", "context_pass")

    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password
        )

    async def create_ldo(
        self,
        cid: str,
        fused_data: Dict[str, Any],
        prediction: Dict[str, Any],
        video_storage_id: Optional[str] = None
    ) -> str:
        """
        Create and store Labeled Data Object

        Args:
            cid: Context ID
            fused_data: Output from CIM fusion
            prediction: AI inference results

        Returns:
            LDO ID
        """
        logger.info(f"💾 Creating LDO for CID: {cid}")

        # Generate LDO ID
        timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
        ldo_id = f"LDO-{timestamp_str}-{cid[-8:]}"

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Insert into metadata_payloads (context + sensor data + video reference)
            payload_data = {
                "context": fused_data["context"],
                "sensor_data": fused_data["sensor_data"],
                "video_storage_id": video_storage_id,
                "video_file": fused_data.get("video_file"),
                "fusion_metadata": {
                    "fusion_timestamp": fused_data["fusion_timestamp"],
                    "fusion_version": fused_data["fusion_version"],
                }
            }

            cur.execute("""
                INSERT INTO metadata_payloads (cid, payload_data, created_at, updated_at, is_mock)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (cid) DO UPDATE
                SET payload_data = EXCLUDED.payload_data,
                    updated_at = EXCLUDED.updated_at
            """, (
                cid,
                Json(payload_data),
                fused_data["timestamp"],
                datetime.now(),
                False  # Real production data
            ))

            # Insert into predictions
            cur.execute("""
                INSERT INTO predictions (
                    ldo_id, device_id, model_version, prediction, confidence,
                    sensor_data, context_data, is_mock, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                ldo_id,
                fused_data["device_id"],
                prediction["model_version"],
                prediction["result"],
                prediction["confidence"],
                Json(fused_data["sensor_data"]),
                Json(fused_data["context"]),
                False,  # Real production data
                fused_data["timestamp"]
            ))

            # If low confidence, add to feedback queue
            if prediction["confidence"] < 0.70:
                priority = "high" if prediction["confidence"] < 0.60 else "normal"
                cur.execute("""
                    INSERT INTO feedback_queue (
                        ldo_id, device_id, prediction, confidence, priority, is_mock, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    ldo_id,
                    fused_data["device_id"],
                    prediction["result"],
                    prediction["confidence"],
                    priority,
                    False,
                    fused_data["timestamp"]
                ))
                logger.info(f"📋 Added to feedback queue (low confidence: {prediction['confidence']:.2%})")

            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"✅ LDO created and stored: {ldo_id}")
            return ldo_id

        except Exception as e:
            logger.error(f"❌ Error creating LDO: {e}", exc_info=True)
            raise
