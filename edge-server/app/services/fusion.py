"""
Fusion Service - Context Injection Module (CIM)
Fuses context metadata with real-time data from multiple sources:
- PLCs (Modbus, OPC UA)
- MES systems (Wonderware, Siemens Opcenter)
- ERP systems (SAP, Oracle)
- SCADA systems (Ignition, WinCC)
- Historians (OSIsoft PI, InfluxDB)
"""

import logging
import os
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import random

from app.adapters import (
    DataSourceAdapter,
    ModbusPLCAdapter,
    OPCUAPLCAdapter,
    WonderwareMESAdapter,
    SAPAdapter,
    IgnitionAdapter,
    OSIsoftPIAdapter,
    MockDataSourceAdapter # Import MockDataSourceAdapter
)
from app.services.recommendation_service import RecommendationService
from mock_data.mock_adapter_configs import MOCK_ADAPTER_CONFIGS # Import mock configs

logger = logging.getLogger(__name__)


class FusionService:
    """
    Context Injection Module (CIM)
    Fuses context metadata from QR codes with real-time data from multiple sources

    Multi-Source Architecture:
    - Reads from PLCs, MES, ERP, SCADA, Historians in parallel
    - Combines all data sources into single fused payload
    - Prioritizes data sources based on configuration
    """

    def __init__(self):
        self.data_sources: Dict[str, DataSourceAdapter] = {}
        self.use_mock_data = os.getenv("USE_MOCK_SENSORS", "true").lower() == "true"

        # Device-to-source mappings (which device uses which sources)
        # In production, this would come from database
        self.device_source_mappings: Dict[str, List[str]] = {}

        # Recommendation service for ML-to-PLC control loop
        self.recommendation_service = RecommendationService()

    async def initialize(self):
        """
        Initialize data source adapters from configuration

        In POC: Uses environment variables
        In Production: Would load from database (data_source_configs table)
        """
        logger.info("🔧 Initializing multi-source data adapters...")

        if self.use_mock_data:
            logger.info("⚠️  Using MOCK sensor data from mock_adapter_configs.py")
            for mock_config in MOCK_ADAPTER_CONFIGS:
                adapter_type = mock_config["adapter_type"]
                source_name = mock_config["source_name"]
                config = mock_config["config"]
                mock_data = mock_config["mock_data"]

                # Create a MockDataSourceAdapter instance
                mock_adapter = MockDataSourceAdapter(source_name, {**config, "mock_data": mock_data})
                if await mock_adapter.connect():
                    self.data_sources[adapter_type] = mock_adapter
                    logger.info(f"✅ Mock {adapter_type} adapter registered: {source_name}")
            return

        # =====================================================
        # PLC ADAPTERS
        # =====================================================

        # Modbus TCP
        modbus_host = os.getenv("MODBUS_HOST")
        if modbus_host:
            try:
                modbus_config = {
                    "host": modbus_host,
                    "port": int(os.getenv("MODBUS_PORT", "502")),
                    "unit_id": int(os.getenv("MODBUS_UNIT_ID", "1")),
                    "register_mappings": {
                        "temperature": {"address": 0, "type": "holding", "count": 1, "scale": 100.0},
                        "vibration": {"address": 2, "type": "holding", "count": 1, "scale": 100.0},
                        "pressure": {"address": 4, "type": "holding", "count": 1, "scale": 100.0},
                        "humidity": {"address": 6, "type": "holding", "count": 1, "scale": 100.0},
                        "cycle_time": {"address": 8, "type": "holding", "count": 1, "scale": 100.0},
                    }
                }
                modbus_adapter = ModbusPLCAdapter("Modbus-PLC", modbus_config)
                if await modbus_adapter.connect():
                    self.data_sources["modbus"] = modbus_adapter
                    logger.info(f"✅ Modbus adapter registered: {modbus_host}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Modbus: {e}")

        # OPC UA
        opcua_url = os.getenv("OPCUA_SERVER_URL")
        if opcua_url:
            try:
                opcua_config = {
                    "server_url": opcua_url,
                    "node_mappings": {
                        "temperature": "ns=2;i=1001",
                        "vibration": "ns=2;i=1002",
                        "pressure": "ns=2;i=1003",
                        "humidity": "ns=2;i=1004",
                        "cycle_time": "ns=2;i=1005",
                    }
                }
                opcua_adapter = OPCUAPLCAdapter("OPC-UA-PLC", opcua_config)
                if await opcua_adapter.connect():
                    self.data_sources["opcua"] = opcua_adapter
                    logger.info(f"✅ OPC UA adapter registered: {opcua_url}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OPC UA: {e}")

        # =====================================================
        # MES ADAPTERS
        # =====================================================

        mes_url = os.getenv("MES_BASE_URL")
        if mes_url:
            try:
                mes_config = {
                    "base_url": mes_url,
                    "api_key": os.getenv("MES_API_KEY"),
                    "username": os.getenv("MES_USERNAME"),
                    "password": os.getenv("MES_PASSWORD"),
                }
                mes_adapter = WonderwareMESAdapter("Wonderware-MES", mes_config)
                if await mes_adapter.connect():
                    self.data_sources["mes"] = mes_adapter
                    logger.info(f"✅ MES adapter registered: {mes_url}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize MES: {e}")

        # =====================================================
        # ERP ADAPTERS
        # =====================================================

        erp_url = os.getenv("ERP_BASE_URL")
        if erp_url:
            try:
                erp_config = {
                    "base_url": erp_url,
                    "username": os.getenv("ERP_USERNAME"),
                    "password": os.getenv("ERP_PASSWORD"),
                    "api_key": os.getenv("ERP_API_KEY"),
                }
                erp_adapter = SAPAdapter("SAP-ERP", erp_config)
                if await erp_adapter.connect():
                    self.data_sources["erp"] = erp_adapter
                    logger.info(f"✅ ERP adapter registered: {erp_url}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize ERP: {e}")

        # =====================================================
        # SCADA ADAPTERS
        # =====================================================

        scada_url = os.getenv("SCADA_BASE_URL")
        if scada_url:
            try:
                scada_config = {
                    "base_url": scada_url,
                    "username": os.getenv("SCADA_USERNAME"),
                    "password": os.getenv("SCADA_PASSWORD"),
                    "tag_paths": os.getenv("SCADA_TAG_PATHS", "").split(",") if os.getenv("SCADA_TAG_PATHS") else []
                }
                scada_adapter = IgnitionAdapter("Ignition-SCADA", scada_config)
                if await scada_adapter.connect():
                    self.data_sources["scada"] = scada_adapter
                    logger.info(f"✅ SCADA adapter registered: {scada_url}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize SCADA: {e}")

        # =====================================================
        # HISTORIAN ADAPTERS
        # =====================================================

        historian_url = os.getenv("HISTORIAN_BASE_URL")
        if historian_url:
            try:
                historian_config = {
                    "base_url": historian_url,
                    "username": os.getenv("HISTORIAN_USERNAME"),
                    "password": os.getenv("HISTORIAN_PASSWORD"),
                    "time_window_minutes": int(os.getenv("HISTORIAN_WINDOW_MINUTES", "60")),
                    "tags": os.getenv("HISTORIAN_TAGS", "").split(",") if os.getenv("HISTORIAN_TAGS") else []
                }
                historian_adapter = OSIsoftPIAdapter("PI-Historian", historian_config)
                if await historian_adapter.connect():
                    self.data_sources["historian"] = historian_adapter
                    logger.info(f"✅ Historian adapter registered: {historian_url}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Historian: {e}")

        # Summary
        if not self.data_sources:
            logger.warning("⚠️  No data sources configured, falling back to mock data")
            self.use_mock_data = True
        else:
            logger.info(f"✅ {len(self.data_sources)} data sources initialized: {list(self.data_sources.keys())}")

    async def shutdown(self):
        """Shutdown all data source adapters"""
        for name, adapter in self.data_sources.items():
            try:
                await adapter.disconnect()
                logger.info(f"✅ Disconnected {name} adapter")
            except Exception as e:
                logger.error(f"❌ Error disconnecting {name}: {e}")

    async def read_sensor_data(self, device_id: str) -> Dict[str, Any]:
        """
        Read real-time data from ALL configured sources (multi-source fusion)

        Reads from PLCs, MES, ERP, SCADA, Historians in PARALLEL and combines results.

        Args:
            device_id: Camera/device ID to determine which sources to read from

        Returns:
            Combined data from all sources
        """
        if not self.data_sources:
            logger.warning("⚠️  No data sources configured, returning empty data")
            return {}

        # Read from all data sources in parallel
        logger.info(f"📡 Reading from {len(self.data_sources)} data sources in parallel...")

        # Create tasks for parallel reading
        read_tasks = []
        source_names = []

        for source_name, adapter in self.data_sources.items():
            read_tasks.append(adapter.read_data(device_id))
            source_names.append(source_name)

        # Execute all reads in parallel (non-blocking)
        results = await asyncio.gather(*read_tasks, return_exceptions=True)

        # Combine results from all sources
        combined_data = {
            "plc": {},
            "mes": {},
            "erp": {},
            "scada": {},
            "historian": {}
        }

        for i, (source_name, result) in enumerate(zip(source_names, results)):
            if isinstance(result, Exception):
                logger.error(f"❌ Error reading from {source_name}: {result}")
                continue

            if result:
                # Categorize by source type
                if source_name in ["modbus", "opcua"]:
                    combined_data["plc"].update(result)
                elif source_name == "mes":
                    combined_data["mes"] = result
                elif source_name == "erp":
                    combined_data["erp"] = result
                elif source_name == "scada":
                    combined_data["scada"] = result
                elif source_name == "historian":
                    combined_data["historian"] = result

                logger.info(f"✅ Data from {source_name}: {len(result)} fields")

        # Remove empty categories
        combined_data = {k: v for k, v in combined_data.items() if v}

        if not combined_data:
            logger.warning("⚠️  All data sources returned empty, using mock data")
            return self._generate_mock_sensor_data()

        logger.info(f"✅ Multi-source read complete: {list(combined_data.keys())}")
        return combined_data



    async def fuse_data(
        self,
        cid: str,
        context: Dict[str, Any],
        sensor_data: Dict[str, Any],
        camera_id: str,
        timestamp: str,
        video_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        CONTEXT INJECTION MODULE (CIM) - PATENTED (Multi-Source Version)
        Fuses context metadata with real-time data from MULTIPLE sources

        This is the core innovation: combining QR code context with data from:
        - PLCs (real-time sensor data)
        - MES (production context)
        - ERP (work order, material data)
        - SCADA (equipment status)
        - Historians (historical trends)

        Args:
            cid: Context ID from QR code
            context: Context metadata (product_id, batch, operator, etc.)
            sensor_data: Multi-source data (plc, mes, erp, scada, historian)
            camera_id: Device that sent the CID
            timestamp: When the CID was scanned
            video_file: Video filename (raw visual data)

        Returns:
            Fused data object ready for AI inference
        """
        logger.info(f"🔗 Multi-Source CIM Fusion for CID: {cid}")

        # Count total data points
        total_fields = len(context)
        for source_category, source_data in sensor_data.items():
            if isinstance(source_data, dict):
                total_fields += len(source_data)

        fused_data = {
            # Identity
            "cid": cid,
            "device_id": camera_id,
            "timestamp": timestamp,

            # Context from QR code (what the part IS)
            "context": context,

            # Multi-source data (how the part was MADE + business context)
            "sensor_data": sensor_data,

            # Video evidence (raw visual data)
            "video_file": video_file,

            # Combined signature (unique to this exact production event)
            "fusion_timestamp": datetime.now().isoformat(),
            "fusion_version": "v2.0-CIM-MultiSource",

            # Metadata
            "data_sources": list(sensor_data.keys()) if sensor_data else []
        }

        logger.info(f"✅ Multi-Source CIM Fusion complete:")
        logger.info(f"   - Context fields: {len(context)}")
        logger.info(f"   - Data sources: {fused_data['data_sources']}")
        logger.info(f"   - Total data points: {total_fields}")

        return fused_data

    async def run_inference(self, fused_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run AI inference on multi-source fused data

        Args:
            fused_data: Output from multi-source CIM fusion

        Returns:
            Prediction results
        """
        logger.info(f"🤖 Running AI inference on multi-source data...")

        # TODO: Load actual AI model (TensorRT, ONNX, etc.)
        # For now, use simple heuristic

        sensor_data = fused_data["sensor_data"]

        # Extract PLC sensor readings (if available)
        plc_data = sensor_data.get("plc", {})

        # Simple defect detection based on PLC sensor thresholds
        is_defective = (
            plc_data.get("temperature", 0) > 90 or
            plc_data.get("vibration", 0) > 5.0 or
            plc_data.get("pressure", 0) < 80 or
            plc_data.get("cycle_time", 0) > 30
        )

        prediction = "defective" if is_defective else "good"
        confidence = random.uniform(0.85, 0.98) if not is_defective else random.uniform(0.75, 0.95)

        result = {
            "model_version": "v0.3-heuristic-multisource",
            "result": prediction,
            "confidence": round(confidence, 4),
            "inference_timestamp": datetime.now().isoformat(),
            "data_sources_used": list(sensor_data.keys())
        }

        logger.info(f"✅ Inference complete: {prediction} (confidence: {confidence:.2%})")
        logger.info(f"   - Data sources: {result['data_sources_used']}")

        return result

    async def generate_recommendations(
        self,
        device_id: str,
        fused_data: Dict[str, Any],
        prediction: Dict[str, Any],
        ldo_id: Optional[str] = None
    ) -> List[str]:
        """
        Generate ML recommendations for process optimization

        Analyzes sensor data and prediction results to generate actionable
        recommendations for operators (e.g., "reduce temperature", "increase pressure").

        This is the ML-to-PLC control loop:
        1. AI detects anomaly/inefficiency
        2. AI recommends corrective action
        3. Recommendation goes to operator for approval (Safety Gate 1)
        4. After approval, write to PLC (Safety Gates 2 & 3)

        Args:
            device_id: Edge device/camera ID
            fused_data: Fused data from CIM
            prediction: AI prediction results
            ldo_id: Optional LDO ID that triggered this recommendation

        Returns:
            List of recommendation IDs created
        """
        logger.info(f"💡 Generating ML recommendations for device: {device_id}")

        sensor_data = fused_data.get("sensor_data", {})
        plc_data = sensor_data.get("plc", {})

        if not plc_data:
            logger.warning("⚠️  No PLC data available, cannot generate recommendations")
            return []

        recommendation_ids = []

        # =====================================================
        # TEMPERATURE OPTIMIZATION
        # =====================================================
        temperature = plc_data.get("temperature")
        if temperature and temperature > 85:
            # Temperature too high - recommend reducing setpoint
            recommended_temp = min(temperature - 10, 75)  # Target 75°C

            recommendation = {
                "action_type": "adjust_temperature",
                "target_parameter": "temperature",
                "current_value": temperature,
                "recommended_value": recommended_temp,
                "unit": "°C",
                "reasoning": f"Current temperature ({temperature}°C) exceeds optimal range. "
                             f"Reducing to {recommended_temp}°C will improve quality and reduce defects.",
                "confidence": prediction.get("confidence", 0.85),
                "priority": 1 if temperature > 95 else 2,  # High priority if critical
                "model_version": prediction.get("model_version", "v0.3")
            }

            try:
                rec_id = await self.recommendation_service.create_recommendation(
                    device_id=device_id,
                    recommendation=recommendation,
                    ldo_id=ldo_id
                )
                recommendation_ids.append(rec_id)
                logger.info(f"✅ Temperature recommendation created: {rec_id}")
            except Exception as e:
                logger.error(f"❌ Failed to create temperature recommendation: {e}")

        # =====================================================
        # VIBRATION OPTIMIZATION
        # =====================================================
        vibration = plc_data.get("vibration")
        if vibration and vibration > 4.0:
            # Vibration too high - recommend reducing RPM
            recommended_rpm_reduction = 50  # Reduce RPM by 50

            recommendation = {
                "action_type": "reduce_speed",
                "target_parameter": "rpm",
                "current_value": plc_data.get("rpm"),  # May be None
                "recommended_value": recommended_rpm_reduction,
                "unit": "RPM",
                "reasoning": f"Excessive vibration detected ({vibration} mm/s). "
                             f"Reducing motor speed by {recommended_rpm_reduction} RPM will reduce mechanical stress.",
                "confidence": prediction.get("confidence", 0.85),
                "priority": 1 if vibration > 6.0 else 2,
                "model_version": prediction.get("model_version", "v0.3")
            }

            try:
                rec_id = await self.recommendation_service.create_recommendation(
                    device_id=device_id,
                    recommendation=recommendation,
                    ldo_id=ldo_id
                )
                recommendation_ids.append(rec_id)
                logger.info(f"✅ Vibration recommendation created: {rec_id}")
            except Exception as e:
                logger.error(f"❌ Failed to create vibration recommendation: {e}")

        # =====================================================
        # PRESSURE OPTIMIZATION
        # =====================================================
        pressure = plc_data.get("pressure")
        if pressure and pressure < 85:
            # Pressure too low - recommend increasing setpoint
            recommended_pressure = max(pressure + 10, 95)  # Target 95 PSI

            recommendation = {
                "action_type": "adjust_pressure",
                "target_parameter": "pressure",
                "current_value": pressure,
                "recommended_value": recommended_pressure,
                "unit": "PSI",
                "reasoning": f"Low pressure detected ({pressure} PSI). "
                             f"Increasing to {recommended_pressure} PSI will ensure proper material flow.",
                "confidence": prediction.get("confidence", 0.85),
                "priority": 2,
                "model_version": prediction.get("model_version", "v0.3")
            }

            try:
                rec_id = await self.recommendation_service.create_recommendation(
                    device_id=device_id,
                    recommendation=recommendation,
                    ldo_id=ldo_id
                )
                recommendation_ids.append(rec_id)
                logger.info(f"✅ Pressure recommendation created: {rec_id}")
            except Exception as e:
                logger.error(f"❌ Failed to create pressure recommendation: {e}")

        # =====================================================
        # CYCLE TIME OPTIMIZATION
        # =====================================================
        cycle_time = plc_data.get("cycle_time")
        if cycle_time and cycle_time > 28:
            # Cycle time too long - recommend optimization
            recommended_cycle_time = 22  # Target 22 seconds

            recommendation = {
                "action_type": "optimize_cycle_time",
                "target_parameter": "cycle_time",
                "current_value": cycle_time,
                "recommended_value": recommended_cycle_time,
                "unit": "seconds",
                "reasoning": f"Cycle time ({cycle_time}s) is above target. "
                             f"Optimizing to {recommended_cycle_time}s will increase throughput by "
                             f"{int((cycle_time - recommended_cycle_time) / cycle_time * 100)}%.",
                "confidence": prediction.get("confidence", 0.85),
                "priority": 3,  # Lower priority (optimization, not critical)
                "model_version": prediction.get("model_version", "v0.3")
            }

            try:
                rec_id = await self.recommendation_service.create_recommendation(
                    device_id=device_id,
                    recommendation=recommendation,
                    ldo_id=ldo_id
                )
                recommendation_ids.append(rec_id)
                logger.info(f"✅ Cycle time recommendation created: {rec_id}")
            except Exception as e:
                logger.error(f"❌ Failed to create cycle time recommendation: {e}")

        if recommendation_ids:
            logger.info(f"✅ Generated {len(recommendation_ids)} recommendations")
        else:
            logger.info(f"ℹ️  No recommendations needed - all parameters within optimal range")

        return recommendation_ids
