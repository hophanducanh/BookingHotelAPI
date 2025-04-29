import json
from models import Locations, Facilities, Hotel, HotelFacilities, HotelImages

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
                if not hotel:
                    policies = json.dumps(hotel_data.get('Policies', []), ensure_ascii=False)
                    hotel = Hotel(
                        hotel_name=hotel_data['Name'],
                        new_price=int(hotel_data['New price']) if hotel_data['New price'] else 0,
                        old_price=int(hotel_data['Old price']) if hotel_data['Old price'] else 0,
                        hotel_star=float(hotel_data['Star']) if hotel_data['Star'] else 0.0,
                        hotel_rating=float(hotel_data['Rating'].replace(',', '.')) if hotel_data['Rating'] else 0.0,
                        address=hotel_data['Location'],
                        policies=policies.replace("\"",""),
                        description=description,
                        id_location=location.id_location,
                        distance = hotel_data['Distance']
                    )
                    db.session.add(hotel)
                    db.session.flush()

                for facility_name in hotel_data['Facilities']:
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