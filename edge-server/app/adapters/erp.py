"""
ERP (Enterprise Resource Planning) Adapters

Supports:
- SAP (OData, REST APIs)
- Oracle ERP Cloud
- Microsoft Dynamics 365
- NetSuite
- Generic REST/SOAP ERP APIs
"""

from typing import Dict, Any, Optional
import logging
import httpx
from datetime import datetime

from .base import DataSourceAdapter

logger = logging.getLogger(__name__)


class ERPAdapter(DataSourceAdapter):
    """
    Generic ERP adapter using REST API

    Retrieves enterprise data:
    - Work orders
    - Material master data
    - Bill of materials (BOM)
    - Inventory levels
    - Quality inspection plans
    - Supplier information
    """

    async def connect(self) -> bool:
        """Test connection to ERP API"""
        try:
            base_url = self.config.get("base_url")
            api_key = self.config.get("api_key")
            username = self.config.get("username")
            password = self.config.get("password")

            if not base_url:
                logger.error(f"❌ ERP adapter {self.source_name}: Missing base_url")
                return False

            # Test health endpoint
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Content-Type": "application/json"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                elif username and password:
                    import base64
                    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                    headers["Authorization"] = f"Basic {credentials}"

                health_endpoint = self.config.get("health_endpoint", "/api/health")
                response = await client.get(f"{base_url}{health_endpoint}", headers=headers)

                if response.status_code in [200, 204]:
                    self.is_connected = True
                    logger.info(f"✅ ERP adapter connected: {self.source_name}")
                    return True
                else:
                    logger.error(f"❌ ERP health check failed: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"❌ ERP connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from ERP"""
        self.is_connected = False
        logger.info(f"✅ ERP adapter disconnected: {self.source_name}")
        return True

    async def read_data(self, identifier: str) -> Dict[str, Any]:
        """
        Read data from ERP

        Args:
            identifier: Work order, material number, or product ID

        Returns:
            ERP data (work order, BOM, quality specs, etc.)
        """
        if not self.is_connected:
            logger.warning(f"⚠️  ERP adapter not connected: {self.source_name}")
            return {}

        try:
            base_url = self.config.get("base_url")
            api_key = self.config.get("api_key")
            username = self.config.get("username")
            password = self.config.get("password")

            # Build headers
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            elif username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"

            # Endpoint for work order data
            endpoint = self.config.get("data_endpoint", "/api/workorders")

            # Make API request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{base_url}{endpoint}/{identifier}",
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()

                    # Extract relevant fields
                    erp_data = {
                        "work_order": data.get("work_order"),
                        "material_number": data.get("material_number"),
                        "material_description": data.get("material_description"),
                        "batch_number": data.get("batch_number"),
                        "production_version": data.get("production_version"),
                        "bom_version": data.get("bom_version"),
                        "routing_version": data.get("routing_version"),
                        "planned_quantity": data.get("planned_quantity"),
                        "uom": data.get("unit_of_measure"),
                        "quality_inspection_plan": data.get("quality_inspection_plan"),
                        "supplier_code": data.get("supplier_code"),
                        "material_cost": data.get("material_cost"),
                        "priority": data.get("priority"),
                        "planned_start_date": data.get("planned_start_date"),
                        "planned_end_date": data.get("planned_end_date"),
                        "customer_order": data.get("customer_order"),
                        "timestamp": data.get("timestamp", datetime.now().isoformat())
                    }

                    logger.info(f"✅ ERP data read: WO={erp_data.get('work_order')}, Material={erp_data.get('material_number')}")
                    return erp_data

                else:
                    logger.error(f"❌ ERP API error: {response.status_code} - {response.text}")
                    return {}

        except Exception as e:
            logger.error(f"❌ ERP read error: {e}", exc_info=True)
            return {}


class SAPAdapter(ERPAdapter):
    """
    SAP ERP adapter
    Uses SAP OData services or REST APIs
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        # Set SAP-specific defaults
        if "data_endpoint" not in config:
            config["data_endpoint"] = "/sap/opu/odata/sap/API_PRODUCTION_ORDER_2_SRV/A_ProductionOrder"
        if "health_endpoint" not in config:
            config["health_endpoint"] = "/sap/public/ping"

        super().__init__(source_name, config)

    async def read_data(self, identifier: str) -> Dict[str, Any]:
        """Read from SAP OData service"""
        if not self.is_connected:
            return {}

        try:
            base_url = self.config.get("base_url")
            api_key = self.config.get("api_key")
            username = self.config.get("username")
            password = self.config.get("password")

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            if api_key:
                headers["APIKey"] = api_key
            elif username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"

            # SAP OData query
            endpoint = self.config.get("data_endpoint")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{base_url}{endpoint}('{identifier}')",
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json().get("d", {})

                    sap_data = {
                        "work_order": data.get("ManufacturingOrder"),
                        "material_number": data.get("Material"),
                        "material_description": data.get("ProductDescription"),
                        "plant": data.get("ProductionPlant"),
                        "planned_quantity": data.get("MfgOrderPlannedTotalQty"),
                        "actual_quantity": data.get("MfgOrderActualReleasedQty"),
                        "order_type": data.get("ManufacturingOrderType"),
                        "priority": data.get("ProductionOrderPriority"),
                        "planned_start_date": data.get("MfgOrderPlannedStartDate"),
                        "planned_end_date": data.get("MfgOrderPlannedEndDate"),
                        "timestamp": datetime.now().isoformat()
                    }

                    logger.info(f"✅ SAP data read: Order={sap_data.get('work_order')}")
                    return sap_data

                else:
                    logger.error(f"❌ SAP API error: {response.status_code}")
                    return {}

        except Exception as e:
            logger.error(f"❌ SAP read error: {e}", exc_info=True)
            return {}


class OracleERPAdapter(ERPAdapter):
    """
    Oracle ERP Cloud adapter
    Uses Oracle REST APIs
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        # Set Oracle-specific defaults
        if "data_endpoint" not in config:
            config["data_endpoint"] = "/fscmRestApi/resources/11.13.18.05/workOrders"
        if "health_endpoint" not in config:
            config["health_endpoint"] = "/fscmRestApi/resources/latest/ping"

        super().__init__(source_name, config)


class MicrosoftDynamicsAdapter(ERPAdapter):
    """
    Microsoft Dynamics 365 adapter
    Uses Dynamics Web API (OData v4)
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        # Set Dynamics-specific defaults
        if "data_endpoint" not in config:
            config["data_endpoint"] = "/api/data/v9.2/msdyn_workorders"
        if "health_endpoint" not in config:
            config["health_endpoint"] = "/api/data/v9.2/WhoAmI"

        super().__init__(source_name, config)

    async def connect(self) -> bool:
        """Connect to Dynamics 365 using OAuth token"""
        try:
            # Dynamics typically uses OAuth 2.0
            client_id = self.config.get("client_id")
            client_secret = self.config.get("client_secret")
            tenant_id = self.config.get("tenant_id")

            if not all([client_id, client_secret, tenant_id]):
                logger.error("❌ Dynamics 365 requires client_id, client_secret, and tenant_id")
                return False

            # TODO: Implement OAuth token retrieval
            # For now, assume API key or token is provided
            self.is_connected = True
            logger.info(f"✅ Dynamics 365 adapter connected: {self.source_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Dynamics 365 connection failed: {e}")
            return False
