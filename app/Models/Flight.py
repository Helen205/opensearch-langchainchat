from pydantic import BaseModel,Field
from typing import Optional, Union
from datetime import date, datetime

class FlightData(BaseModel):
    AvgTicketPrice: Optional[float] = Field(None, description="Ortalama Bilet Fiyatı")
    Cancelled: Optional[bool] = Field(None, description="İptal Edildi")
    Carrier: Optional[str] = Field(None, description="Taşıyıcı")
    Dest: Optional[str] = Field(None, description="Varış Noktası")
    DestAirportID: Optional[str] = Field(None, description="Varış Havalimanı ID")
    DestCityName: Optional[str] = Field(None, description="Varış Şehri Adı")
    DestCountry: Optional[str] = Field(None, description="Varış Ülkesi")
    DestLocation: Optional[str] = Field(None, description="Varış Konumu (geo_point)")
    DestRegion: Optional[str] = Field(None, description="Varış Bölgesi")
    DestWeather: Optional[str] = Field(None, description="Varış Hava Durumu")
    DistanceKilometers: Optional[float] = Field(None, description="Mesafe (Kilometre)")
    DistanceMiles: Optional[float] = Field(None, description="Mesafe (Mil)")
    FlightDelay: Optional[bool] = Field(None, description="Uçuş Gecikmesi")
    FlightDelayMin: Optional[int] = Field(None, description="Uçuş Gecikme Süresi (Dakika)")
    FlightDelayType: Optional[str] = Field(None, description="Uçuş Gecikme Türü")
    FlightNum: Optional[str] = Field(None, description="Uçuş Numarası")
    FlightTimeHour: Optional[str] = Field(None, description="Uçuş Süresi (Saat)")
    FlightTimeMin: Optional[float] = Field(None, description="Uçuş Süresi (Dakika)")
    Origin: Optional[str] = Field(None, description="Kalkış Noktası")
    OriginAirportID: Optional[str] = Field(None, description="Kalkış Havalimanı ID")
    OriginCityName: Optional[str] = Field(None, description="Kalkış Şehri Adı")
    OriginCountry: Optional[str] = Field(None, description="Kalkış Ülkesi")
    OriginLocation: Optional[str] = Field(None, description="Kalkış Konumu (geo_point)")
    OriginRegion: Optional[str] = Field(None, description="Kalkış Bölgesi")
    OriginWeather: Optional[str] = Field(None, description="Kalkış Hava Durumu")
    dayOfWeek: Optional[str] = Field(None, description="Haftanın Günü")
    timestamp: Optional[datetime] = Field(None, description="Zaman Damgası")

class UpdateOriginCityFlightData(BaseModel):
    OriginCityName: Optional[str] = Field(None, description="Kalkış Şehri Adı")

class KelepirData(BaseModel):
    OriginCityName: Optional[str] = Field(None, description="Kalkış Şehri Adı")
    DestCityName: Optional[str] = Field(None, description="Varış Şehri Adı")
    AvgTicketPrice: Optional[float] = Field(None, description="Ortalama Bilet Fiyatı")
    DistanceKilometers: Optional[float] = Field(None, description="Mesafe (Kilometre)")
    FlightDelay: Optional[bool] = Field(None, description="Uçuş Gecikmesi")
    FlightTimeMin: Optional[float] = Field(None, description="Uçuş Süresi (Dakika)")