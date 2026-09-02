from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FinancialItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    displayName: Optional[str] = None
    key: str
    value: Optional[str] = None
    qoQComp: Optional[str] = None
    yqoQComp: Optional[str] = None


class StockFinancialMap(BaseModel):
    model_config = ConfigDict(extra="allow")

    CAS: list[FinancialItem] = Field(default_factory=list)
    BAL: list[FinancialItem] = Field(default_factory=list)
    INC: list[FinancialItem] = Field(default_factory=list)

    @field_validator("CAS", "BAL", "INC", mode="before")
    @classmethod
    def none_to_empty_list(cls, value):
        return value or []


class FinancialPeriod(BaseModel):
    model_config = ConfigDict(extra="allow")

    stockFinancialMap: StockFinancialMap
    FiscalYear: str
    EndDate: str
    Type: str
    StatementDate: Optional[str] = None
    fiscalPeriodNumber: Optional[int] = None


class CurrentPrice(BaseModel):
    BSE: Optional[str] = None
    NSE: Optional[str] = None


class TechnicalData(BaseModel):
    days: int
    bsePrice: Optional[str] = None
    nsePrice: Optional[str] = None


class CompanyProfile(BaseModel):
    model_config = ConfigDict(extra="allow")

    companyDescription: Optional[str] = None
    mgIndustry: Optional[str] = None
    isInId: Optional[str] = None
    exchangeCodeBse: Optional[str] = None
    exchangeCodeNse: Optional[str] = None


class StockDetails(BaseModel):
    model_config = ConfigDict(extra="allow")

    companyName: str
    industry: Optional[str] = None
    companyProfile: Optional[CompanyProfile] = None
    currentPrice: Optional[CurrentPrice] = None
    stockTechnicalData: list[TechnicalData] = Field(default_factory=list)
    percentChange: Optional[str] = None
    yearHigh: Optional[str] = None
    yearLow: Optional[str] = None
    financials: list[FinancialPeriod] = Field(default_factory=list)