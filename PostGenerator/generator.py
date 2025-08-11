import asyncio

import aiohttp
import requests
from aiohttp import ClientTimeout

from config import BASE_SERVER_URL


class PostGenerator:
    def __init__(self, lot_id, auction):
        self.lot_id = lot_id
        self.auction = auction
        self.lot_data = None
        self.calculator_data = None

    async def initialize(self):
        await self._load_lot_data()
        await self._load_calculator_data()

    async def _load_lot_data(self):
        self.lot_data = await self.get_lot()

    async def _load_calculator_data(self):
        self.calculator_data = await self.get_calculator_data()

    async def get_lot(self):
        url = f'{BASE_SERVER_URL}api/v1/auction-vehicles/get-vin-or-lot/?vin_or_lot={self.lot_id}&auction={self.auction}'

        try:
            async with aiohttp.ClientSession(timeout=ClientTimeout(5)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"Failed to get lot data: {response.status}")
                        return None

                    data = await response.json()
                    return data

        except Exception as e:
            print(f"Error getting lot data: {e}")
            return None

    async def get_calculator_data(self):
        data = {
            'price': 1000,
            'lot_id': self.lot_id,
            'auction': self.auction
        }

        url = f'{BASE_SERVER_URL}api/v1/calculator/'

        try:
            async with aiohttp.ClientSession(timeout=ClientTimeout(5)) as session:
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        print(f"Failed to get calculator data: {response.status}")
                        return None

                    response_data = await response.json()
                    print(response_data)
                    return response_data

        except Exception as e:
            print(f"Error getting calculator data: {e}")
            return None

    def get_minimal_prices(self):
        if not self.calculator_data:
            return {
                'broker_fee': 0,
                'transportation_price': 0,
                'ocean_ship': 0,
                'additional': 0,
                'totals': 0
            }

        prices = self.calculator_data['calculator']
        min_prices = {
            'broker_fee': prices.get('broker_fee', 0),
            'transportation_price': min(prices.get('transportation_price', {}).values()) if prices.get(
                'transportation_price') else 0,
            'ocean_ship': min(prices.get('ocean_ship', {}).values()) if prices.get('ocean_ship') else 0,
            'additional': prices.get('additional', 0),
            'totals': min(prices.get('totals', {}).values()) if prices.get('totals') else 0
        }
        return min_prices

    def get_first_three_images(self):
        if not self.lot_data or 'VehicleImages' not in self.lot_data:
            return []

        images = self.lot_data['VehicleImages']
        if len(images) > 3:
            images = images[:3]
        return images

    def generate_text(self, comment=''):
        if not self.lot_data or not self.calculator_data:
            return "Ошибка: данные не загружены"

        prices = self.get_minimal_prices()
        reserve_price = self.lot_data.get('ReservePrice')
        text = (
            f"https://bidauto.online/lot/{self.lot_id}?auction_name={self.auction.upper()}\n\n"
            f"📲Susisiekite : https://t.me/bidautoLT\n"
            f"🚗🔥 Labai geras pasiūlymas aukcione! 🔥🚗\n"
            f"🚗 <b>{self.lot_data.get('Year')} {self.lot_data.get('Make')} {self.lot_data.get('ModelGroup')}</b>\n"
            f"🕔 <b>{self.lot_data.get('Odometer')} miles</b>\n"
            f"⚠️ <u><b>REZERVAS: ${f"{reserve_price:,}" if reserve_price else 'N/A'}</b></u>\n"
            f"📌 Pardavėjas: Draudimas 👍\n"
            f"📌 VIN: {self.lot_data['VIN']}\n"
            f"📌 Būklė: {self.lot_data['LotCondition']}\n"
            f"📌 Dokumentai: Tinka registracijai 👍\n"
            f"🛳️ Transporto išlaidos sudarys:\n"
            f"Vietinis Transportas: ${prices['transportation_price']}\n"
            f"Jūrinis pervežimas: ${prices['ocean_ship']}\n"
            f"Broker Fee: ${prices['broker_fee']}\n"
            f"***Taip pat prisides aukciono mokesčiai kurie priklauso nuo statymo sumos!\n"
            f"🇱🇹 Lietuvoje liks sumokėti:\n"
            f"✅ 10% Muitas\n"
            f"✅ 21% PVM\n"
            f"✅ 350€ Krova\n"
            f"⏳ Liko mažai laiko – nepraleiskite progos! ⏳💨\n"
            f"✉️ Rašykite mums DM arba apsilankykite 👉 bidauto.online\n\n"
            f"{f'<b>{comment}</b>' if comment else ''}\n\n"
        )
        return text
