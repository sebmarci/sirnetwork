import pandas as pd
import eurostat
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

year = 2022

def fetch_eu_air_traffic():
    print("1. Fetching Eurostat Air Traffic Data...")
    # Dataset 'avia_paocc' = Passenger transport by partner country
    # Note: Eurostat datasets are massive. We download it and filter it.
    dataset_code = 'avia_paocc'
    
    try:
        df = eurostat.get_data_df(dataset_code)
        year_col = str(year)
        if year_col in df.columns:
            # Filter columns: reporting country (geo), partner country (partner), and traffic
            df_traffic = df[['geo\\time', 'partner', year_col]].dropna()
            df_traffic.rename(columns={'geo\\time': 'Origin', 'partner': 'Destination', year_col: 'Passengers'}, inplace=True)
            print(f"   -> Successfully loaded {len(df_traffic)} traffic records.")
            return df_traffic
        else:
            print("   -> Year not found in dataset. Please check Eurostat column names.")
            return None
    except Exception as e:
        print(f"Failed to fetch Eurostat data: {e}")
        return None

def get_city_coordinates(city_list):
    print("\n2. Geocoding Cities (Fetching Lat/Lon)...")
    # Nominatim requires a unique user-agent
    geolocator = Nominatim(user_agent="eu_disease_model_research")
    
    geo_data = []
    
    for city in city_list:
        try:
            location = geolocator.geocode(city, timeout=10)
            if location:
                geo_data.append({
                    'City': city,
                    'Lat': location.latitude,
                    'Lon': location.longitude
                })
                print(f"   -> Found: {city} ({location.latitude}, {location.longitude})")
            else:
                print(f"   -> Could not find: {city}")
                
            # CRITICAL: Nominatim allows max 1 request per second. 
            # We sleep for 1 second to avoid getting our IP banned.
            time.sleep(1) 
            
        except GeocoderTimedOut:
            print(f"   -> Timeout looking up: {city}")
            time.sleep(2)
            
    return pd.DataFrame(geo_data)

def main():
    df_traffic = fetch_eu_air_traffic()
    
    if df_traffic is not None:
        # Eurostat uses country codes (e.g., 'FR', 'DE'). 
        unique_nodes = df_traffic['Origin'].unique()
        
        # (Optional) Map Eurostat codes to actual city names for the geocoder
        # Example mapping dictionary:
        code_to_city = {'FR': 'Paris, France', 'DE': 'Berlin, Germany', 'IT': 'Rome, Italy', 'ES': 'Madrid, Spain'}
        
        # Filter our unique nodes to only the ones in our dictionary to keep the test quick
        cities_to_lookup = [code_to_city[code] for code in unique_nodes if code in code_to_city]
        
        df_nodes = get_city_coordinates(cities_to_lookup)
        
        # --- STEP 4: Fetch Populations ---
        # Note: Nominatim does not reliably return populations.
        # To automate this step, you would hit the free REST Countries API or GeoNames here.
        # Let's add a placeholder column for where your API call would go:
        print("\n3. Fetching Populations (Placeholder for REST Countries API)...")
        df_nodes['Population'] = 10000000 # Placeholder: 10M
        
        # --- STEP 5: Export to your SIR Model ---
        print("\n4. Exporting combined data for SIR Model...")
        df_nodes.to_csv("eu_model_nodes.csv", index=False)
        df_traffic.to_csv("eu_model_edges_traffic.csv", index=False)
        print("   -> Success! Saved 'eu_model_nodes.csv' and 'eu_model_edges_traffic.csv'.")

if __name__ == "__main__":
    main()