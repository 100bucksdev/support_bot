import requests

from config import BASE_SERVER_URL


class PostGenerator:
    def __init__(self, lot_id, auction):
        self.lot_id = lot_id
        self.auction = auction
        self.lot_data = self.get_lot()
        self.calculator_data = self.get_calculator_data()

    def get_lot(self):
        response = requests.get(f'{BASE_SERVER_URL}api/v1/auction-vehicles/get-vin-or-lot/?vin_or_lot={self.lot_id}&auction={self.auction}')
        if response.status_code != 200:
            return None
        data = response.json()

        return data

    def get_calculator_data(self):
        data = {
            'price': 1000,
            'lot_id': self.lot_id,
            'auction': self.auction
        }
        response = requests.post(f'{BASE_SERVER_URL}api/v1/calculator/', json=data)
        if response.status_code != 200:
            return None
        data = response.json()
        print(data)
        return data
    def get_minimal_prices(self):
        prices = self.calculator_data['calculator']
        min_prices = {
            'broker_fee': prices['broker_fee'],
            'transportation_price': min(prices['transportation_price'].values()),
            'ocean_ship': min(prices['ocean_ship'].values()),
            'additional': prices['additional'],
            'totals': min(prices['totals'].values())
        }
        return min_prices

    def get_first_three_images(self):
        images = self.lot_data['VehicleImages']
        if len(images) > 3:
            images = images[:3]
        return images

    def generate_text(self, comment=''):
        prices = self.get_minimal_prices()
        text = (
            f"https://bidauto.online/lot/{self.lot_id}?auction_name={self.auction.upper()}\n\n"
            f"🚗🔥 Labai geras pasiūlymas aukcione! 🔥🚗\n"
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
