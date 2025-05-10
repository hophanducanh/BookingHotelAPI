import json
from extensions import db
from models import Locations, Facilities, Hotel, HotelFacilities, HotelImages, Hotel_Room


def normalize_facility_name(name):
    return ' '.join(name.strip().lower().split())

def import_data(db):
    try:
        with open('output.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        for location_data in data:
            city = location_data['city']
            country = 'Việt Nam'
            location = Locations.query.filter_by(city=city, country=country).first()
            if not location:
                location = Locations(name=city, country=country, city=city)
                db.session.add(location)
        db.session.commit()

        all_facilities = set()
        for location_data in data:
            for hotel_data in location_data['Hotel']:
                if hotel_data['Name']:
                    for facility in hotel_data['Facilities']:
                        normalized_facility = normalize_facility_name(facility)
                        all_facilities.add(normalized_facility)

        for facility_name in all_facilities:
            facility = Facilities.query.filter_by(name=facility_name).first()
            if not facility:
                facility = Facilities(name=facility_name, description=facility_name)
                db.session.add(facility)
        db.session.commit()

        for location_data in data:
            city = location_data['city']
            location = Locations.query.filter_by(city=city, country='Việt Nam').first()

            for hotel_data in location_data['Hotel']:
                if not hotel_data['Name']:
                    continue

                hotel = Hotel.query.filter_by(hotel_name=hotel_data['Name']).first()
                description = '\n'.join(hotel_data.get('Description', [])) if hotel_data.get('Description') else ''

                # Convert policies to string
                policies = hotel_data.get('Policies', '')
                if isinstance(policies, dict) or isinstance(policies, list):
                    policies = json.dumps(policies, ensure_ascii=False)

                if not hotel:
                    try:
                        hotel = Hotel(
                            hotel_name=hotel_data['Name'],
                            new_price=int(hotel_data['New price'].replace(',', '')) if hotel_data.get(
                                'New price') else 0,
                            old_price=int(hotel_data['Old price'].replace(',', '')) if hotel_data.get(
                                'Old price') else 0,
                            hotel_star=float(hotel_data['Star']) if hotel_data.get('Star') else 0.0,
                            hotel_rating=float(hotel_data['Rating'].replace(',', '.')) if hotel_data.get(
                                'Rating') else 0.0,
                            address=hotel_data.get('Location', ''),
                            policies=policies,
                            description=description,
                            distance=hotel_data.get('Distance', ''),
                            id_location=location.id_location
                        )
                        db.session.add(hotel)
                        db.session.flush()
                    except ValueError as ve:
                        print(f"Error processing hotel {hotel_data['Name']}: {str(ve)}")
                        continue

                # Import Hotel Facilities
                for facility_name in hotel_data.get('Facilities', []):
                    normalized_facility = normalize_facility_name(facility_name)
                    facility = Facilities.query.filter_by(name=normalized_facility).first()
                    if facility:
                        hotel_facility = HotelFacilities.query.filter_by(
                            id_hotel=hotel.id, id_facilities=facility.id_fac
                        ).first()
                        if not hotel_facility:
                            hotel_facility = HotelFacilities(
                                id_hotel=hotel.id,
                                id_facilities=facility.id_fac
                            )
                            db.session.add(hotel_facility)

                for image_url in hotel_data.get('Images', []):
                    image = HotelImages.query.filter_by(hotel_id=hotel.id, image_url=image_url).first()
                    if not image:
                        image = HotelImages(
                            hotel_id=hotel.id,
                            image_url=image_url
                        )
                        db.session.add(image)

        db.session.commit()
        print("Data imported successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error importing data: {str(e)}")
        raise