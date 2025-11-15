from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any
from datetime import date, datetime


class ItemFactura(BaseModel):
   
    SKU: Optional[str] = ""
    Description: Optional[str] = ""
    Quantity: Optional[str] = ""
    UnitOfMeasurement: Optional[str] = "" # Opcional indica que se deja vacio si el campo en el archivo JSON esta vacio
    UnitPrice: Optional[str] = ""
    NetValuePerItem: Optional[str] = ""
    Currency: Optional[str] = ""
    HSCode: Optional[str] = ""
    Weight: Optional[str] = ""
    BatchOrLotNumber: Optional[str] = ""
    NumberOfPackagesBoxes: Optional[str] = ""
    
    def get_quantity_float(self) -> float:
        try:
            return float(self.Quantity.replace(",", ""))
        except:
            return 0.0
    
    def get_unit_price_float(self) -> float:
        try:
            return float(self.UnitPrice.replace(",", ""))
        except:
            return 0.0
    
    def get_net_value_float(self) -> float:
        try:
            return float(self.NetValuePerItem.replace(",", ""))
        except:
            return 0.0


class Field(BaseModel):

    Fields: str
    Value: str


class FacturaComercial(BaseModel):

    Fields: List[Field]
    Table: List[ItemFactura]
    
    #Extraer campos
    
    def get_field(self, nombre: str) -> str:
        for field in self.Fields:
            if field.Fields == nombre:
                return field.Value
        return ""
    
    # ==================== PROPIEDADES PARA ACCESO RÁPIDO ====================
    
    @property
    def supplier(self) -> str:
        return self.get_field("Supplier")
    
    @property
    def customer(self) -> str:
        return self.get_field("Customer")
    
    @property
    def supplier_address(self) -> str:
        return self.get_field("SupplierAddress")
    
    @property
    def customer_address(self) -> str:
        return self.get_field("CustomerAddress")
    
    @property
    def supplier_tax_id(self) -> str:
        return self.get_field("SupplierTaxID")
    
    @property
    def customer_tax_id(self) -> str:
        return self.get_field("CustomerTaxID")
    
    @property
    def invoice_number(self) -> str:
        return self.get_field("InvoiceNumber")
    
    @property
    def invoice_date(self) -> str:
        return self.get_field("InvoiceDate")
    
    @property
    def incoterm(self) -> str:
        return self.get_field("Incoterm")
    
    @property
    def currency(self) -> str:
        return self.get_field("Currency")
    
    @property
    def total_invoice_value(self) -> str:
        return self.get_field("TotalInvoiceValue")
    
    @property
    def invoice_type(self) -> str:
        return self.get_field("InvoiceType")
    
    @property
    def port_of_loading(self) -> str:
        return self.get_field("PortOfLoading")
    
    @property
    def port_of_discharge(self) -> str:
        return self.get_field("PortOfDischarge")
    
    @property
    def country_of_origin(self) -> str:
        return self.get_field("CountryOfOrigin")
    
    @property
    def payment_terms(self) -> str:
        return self.get_field("PaymentTerms")
    
    #Metodos de conversion
    
    def get_total_float(self) -> float:
        try:
            return float(self.total_invoice_value.replace(",", ""))
        except:
            return 0.0
    
    def parse_date(self) -> Optional[date]:
        date_str = self.invoice_date.strip()
        if not date_str:
            return None
        
        # Lista de formatos de fecha a intentar
        formats = [
            "%Y-%m-%d",           # 2025-01-29
            "%m/%d/%Y",           # 12/23/2024
            "%d-%b-%Y",           # 07-MAY-2025
            "%d/%m/%Y"            # 29/01/2025
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        
        return None
    
    #Metodo exportar
    
    def to_simple_dict(self) -> Dict:
        
        return {
            "supplier": self.supplier,
            "customer": self.customer,
            "supplier_address": self.supplier_address,
            "customer_address": self.customer_address,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date,
            "incoterm": self.incoterm,
            "currency": self.currency,
            "country_of_origin": self.country_of_origin,
            "total_value": self.total_invoice_value,
            "port_of_loading": self.port_of_loading,
            "port_of_discharge": self.port_of_discharge,
            "items_count": len(self.Table),
            "payment_terms": self.payment_terms
        }
