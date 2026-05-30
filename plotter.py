import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np
import imageio
import os
import pandas as pd

def generate_gif(time, S, I, R, eurostat_codes):
    # ==========================================
    # 1. SETUP MAP GEOMETRY (GeoPandas 1.0 Fix)
    # ==========================================
    print("1. Downloading map geometry from Natural Earth...")
    url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
    world = gpd.read_file(url)
    world.rename(columns={'CONTINENT': 'continent', 'NAME': 'name', 'ISO_A3': 'iso_a3'}, inplace=True)

    # Patch France and Norway before filtering
    world.loc[world['name'] == 'France', 'iso_a3'] = 'FRA'
    world.loc[world['name'] == 'Norway', 'iso_a3'] = 'NOR'

    # Filter to Europe and remove missing data codes
    europe = world[(world.continent == 'Europe') & (world.name != 'Russia')].copy()
    europe = europe[europe.iso_a3 != '-99']

    # ==========================================
    # 2. SETUP NODES AND DICTIONARY
    # ==========================================
    print("2. Setting up nodes and translating Eurostat to ISO3...")
    eurostat_to_iso3 = {
        'AT': 'AUT', 'BA': 'BIH', 'BE': 'BEL', 'BG': 'BGR', 'CH': 'CHE', 
        'CY': 'CYP', 'CZ': 'CZE', 'DE': 'DEU', 'DK': 'DNK', 'EE': 'EST', 
        'EL': 'GRC', 'ES': 'ESP', 'FI': 'FIN', 'FR': 'FRA', 'HR': 'HRV', 
        'HU': 'HUN', 'IE': 'IRL', 'IS': 'ISL', 'IT': 'ITA', 'LT': 'LTU', 
        'LU': 'LUX', 'LV': 'LVA', 'ME': 'MNE', 'MK': 'MKD', 'MT': 'MLT', 
        'NL': 'NLD', 'NO': 'NOR', 'PL': 'POL', 'PT': 'PRT', 'RO': 'ROU', 
        'RS': 'SRB', 'SE': 'SWE', 'SI': 'SVN', 'SK': 'SVK', 'TR': 'TUR'
    }

    # Translate your list
    modeled_iso3_codes = [eurostat_to_iso3[code] for code in eurostat_codes]

    # Generate Mock SIR Data (Replace this with your actual array!)
    # Shape: [30 Days, 35 Countries, 3 Compartments]
    sir_data = np.stack((S.T, I.T, R.T), axis=-1)
    sir_data = sir_data / sir_data.sum(axis=2, keepdims=True)

    # ==========================================
    # 3. RENDER FRAMES TO TEMP FOLDER
    # ==========================================
    print("3. Generating frames...")
    filenames = []
    if not os.path.exists('temp_frames'):
        os.makedirs('temp_frames')

    for t in range(time):
        fig, axs = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle(f'EU Disease Spread - Day {t}', fontsize=16)
        
        day_data = sir_data[t]
        
        # Pack this day's data into a DataFrame alongside the correct ISO3 codes
        df_day = pd.DataFrame({
            'ISO3': modeled_iso3_codes,
            'Color_S': [ (0, s, 0) for s in day_data[:, 0] ],
            'Color_I': [ (i, 0, 0) for i in day_data[:, 1] ],
            'Color_R': [ (0, 0, r) for r in day_data[:, 2] ],
            'Color_Comb': [ (i, s, r) for i, s, r in day_data ]
        })
        
        # MERGE: Align the simulated data exactly to the map geometry
        europe_merged = europe.merge(df_day, left_on='iso_a3', right_on='ISO3', how='left')
        
        # Catch un-modeled countries (e.g. UK) and paint them light grey
        for col in ['Color_S', 'Color_I', 'Color_R', 'Color_Comb']:
            europe_merged[col] = europe_merged[col].apply(
                lambda x: x if isinstance(x, tuple) else (0.9, 0.9, 0.9)
            )
        
        # Define mapping for the 4 subplots
        plot_configs = [
            (axs[0, 0], 'Color_S', 'Susceptible (Green)'),
            (axs[0, 1], 'Color_I', 'Infected (Red)'),
            (axs[1, 0], 'Color_R', 'Recovered (Blue)'),
            (axs[1, 1], 'Color_Comb', 'Combined (RGB)')
        ]
        
        # Draw the maps
        for ax, color_col, title in plot_configs:
            europe_merged.plot(ax=ax, color=europe_merged[color_col], edgecolor='black', linewidth=0.5)
            ax.set_title(title)
            ax.set_xlim(-25, 45)
            ax.set_ylim(35, 75)
            ax.axis('off') 
        
        # Save the frame
        filename = f'temp_frames/frame_{t:03d}.png'
        plt.tight_layout()
        plt.savefig(filename, dpi=100, bbox_inches='tight', facecolor='white')
        plt.close(fig) 
        filenames.append(filename)
        
        if t % 5 == 0:
            print(f"   -> Rendered Day {t}/{len(time)-1}")

    # ==========================================
    # 4. STITCH INTO GIF
    # ==========================================
    print("4. Stitching into GIF...")
    gif_path = 'sir_eu_model_2x2.gif'

    with imageio.get_writer(gif_path, mode='I', fps=4) as writer:
        for filename in filenames:
            image = imageio.imread(filename)
            writer.append_data(image)

    # Cleanup temporary PNG files
    for filename in filenames:
        os.remove(filename)
    os.rmdir('temp_frames')

    print(f"Success! GIF saved as: {gif_path}")