import pandas as pd
import dash
from dash import dcc, html,Input, Output, State
import plotly.graph_objs as go
import dash_table
from dash import callback_context

import pandas as pd
import pvlib
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS
import itertools
import matplotlib.pyplot as plt
from pvlib.iotools import get_pvgis_hourly


global_energy_data = pd.DataFrame(columns=['Date', 'Energy_kWh'])
consumption_graph = pd.DataFrame()

# Location information
latitude = 38.962946
longitude = -9.403689
tz = 'Europe/Lisbon'
surface_tilt = 35
surface_azimuth = 180
albedo = 0.2
location = Location(latitude=latitude, longitude=longitude, tz=tz)

Demand_house = pd.read_csv('Janeiro.csv')
Machines_list = pd.read_csv('maquinas.csv')
Irrigation = pd.read_csv('bombas de irrigação.csv')
days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
df_days_of_week = pd.DataFrame(days_of_week, columns=['Day'])

Demand_house['Date'] = pd.to_datetime(Demand_house['Data'] + ' ' + Demand_house['Hora'])
hourly_data = Demand_house.groupby(Demand_house['Date'].dt.floor('H')).agg({'Consumo registado (kW)': 'sum'})
hourly_data.reset_index(inplace=True)
hourly_data.iloc[0, 0] = hourly_data.iloc[0, 0].strftime('%d-%m-%Y %H')
hourly_data['Day of Week'] = hourly_data['Date'].dt.day_name()
hourly_data['Month'] = hourly_data['Date'].dt.month
def get_season_number(month):
    if 3 <= month <= 5:
        return 1  # Spring
    elif 6 <= month <= 8:
        return 2  # Summer
    elif 9 <= month <= 11:
        return 3  # Autumn
    else:
        return 4  # Winter

hourly_data['Season Number'] = hourly_data['Month'].apply(get_season_number)
hourly_data['Continuous_machines'] = 0
hourly_data['Seasonal_machines'] = 0
hourly_data['Pot'] = 0


Districs = {
    'District': ['Aveiro', 'Beja', 'Braga', 'Bragança', 'Castelo Branco', 'Coimbra', 'Évora', 'Faro',
                 'Guarda', 'Leiria', 'Lisboa', 'Portalegre', 'Porto', 'Santarém', 'Setúbal', 'Viana do Castelo',
                 'Vila Real', 'Viseu'],
    'Latitude': [40.6443, 38.0147, 41.5333, 41.8089, 39.8938, 40.2033, 38.5667, 37.0194,
                 40.5373, 39.7436, 38.7223, 39.2967, 41.1496, 39.2362, 38.5244, 41.6935,
                 41.3000, 40.6566],
    'Longitude': [-8.6455, -7.8635, -8.4201, -6.7579, -7.4811, -8.4103, -7.9000, -7.9307,
                  -7.2671, -8.8069, -9.1393, -7.4286, -8.6108, -8.6851, -8.8921, -8.8326,
                  -7.8000, -7.9139]
}
Districs = pd.DataFrame(Districs)

print(hourly_data)
print(hourly_data.info())
app = dash.Dash(__name__, suppress_callback_exceptions=True)


app.layout = html.Div([
    html.Div(
        [
            html.H1(children='Amarna', style={'text-align': 'center'}),
            html.Div(children='''Minimun Value Product''', style={'text-align': 'center'}),
        ],
        style={'margin': 'auto', 'width': '50%'}
    ),
    dcc.Tabs([
        dcc.Tab(label='Input', children=[
            html.H2(children="Let's gather some key details about your needs, so we can estimate how our service could make a difference for you. Put your information that you recall and then click the bottom in the end to see the results"),

            html.Label('What district are you in?'),
            dcc.Dropdown(
                id='District',
                options=[{'label': district, 'value': district} for district in Districs['District']],
                value='Lisboa',
            ),

            html.Br(),  # Add a line break for better separation

            html.H3(children='Irrigation', style={'font-weight': 'bold'}),
            html.Label('Do you have a irrigation System?'),
            dcc.Dropdown(
                id='Irrigation',
                options=[
                    {'label': 'No', 'value': 'No'},
                    {'label': 'Yes', 'value': 'Yes'}
                ],
                value='No',
            ),
            html.Label('Enter the number of hectares:'),
            dcc.Dropdown(
                id='hectares',
                options=[
                    {'label': '[0,10]', 'value': '1'},
                    {'label': '[11,50]', 'value': '2'},
                    {'label': '[51,100]', 'value': '3'},
                    {'label': '[101,300]', 'value': '4'}
                ],
                value='1'
            ),
            html.Label('Number of hours per day for irrigation (usually 1-5):'),
            dcc.Input(
                id='hours_per_day',
                type='number',
                placeholder='Enter hours per day',
                value=0
            ),


            html.Br(),  # Add a line break for better separation

            html.H3(children='Continuous Machines', style={'font-weight': 'bold'}),
            html.Label('Do you have machines that work all year?'),
            dcc.Dropdown(
                id='Continuous_Machine',
                options=[
                    {'label': 'No', 'value': 'No'},
                    {'label': 'Yes', 'value': 'Yes'}
                ],
                value='No',
            ),
            html.Label('Enter the machines you usually use:'),
            dcc.Dropdown(
                id='machine-dropdown',
                options=[{'label': row[0], 'value': row[0]} for row in Machines_list.values],
                value=[Machines_list.values[0][0]],  # Set default value to the first machine
                multi=True
            ),
            html.Label('Select day(s) of the week:'),
            dcc.Dropdown(
                id='select-day-dropdown',
                options=[{'label': day, 'value': day} for day in df_days_of_week['Day']],
                value=[df_days_of_week.iloc[0, 0]],  # Set default value to the first day of the week
                multi=True
            ),
            html.Label('How many hours per day :'),
            dcc.Input(
                id='hours_per_day_1',
                type='number',
                placeholder='Enter hours per day',
                value=0
            ),

            html.Br(),  # Add a line break for better separation

            html.H3(children='Seasonal Machines', style={'font-weight': 'bold'}),

            html.Label('Do you have machines that work in a specific season of the year?'),
            # Seasonal Machine
            dcc.Dropdown(
                id='Seasonal_Machine',
                options=[
                    {'label': 'No', 'value': 'No'},
                    {'label': 'Yes', 'value': 'Yes'}
                ],
                value='No',
            ),
            html.Label('Enter the machines you usually use:'),
            dcc.Dropdown(
                id='machine-dropdown_Seasonal',
                options=[{'label': row[0], 'value': row[0]} for row in Machines_list.values],
                value=[Machines_list.values[0][0]],
                multi=True
            ),
            html.Label('Which season do you work in the most? (1-Spring/2-Summer/3-Autumn/4-Winter):'),
            dcc.Input(
                id='Season',
                type='number',
                placeholder='Enter hours per day',
                value=0
            ),
            html.Br(),  # Add a line break for better separation
            html.Label('Select day(s) of the week:'),
            dcc.Dropdown(
                id='select-day-dropdown_seasonal',
                options=[{'label': day, 'value': day} for day in df_days_of_week['Day']],
                value=[df_days_of_week.iloc[0, 0]],
                multi=True
            ),
            html.Label('How many hours per day :'),
            dcc.Input(
                id='hours_per_day_2',
                type='number',
                placeholder='Enter hours per day',
                value=0
            ),

            html.Br(),
            html.Button("Click to start", id="add-column-button"),
            html.Div(id='output-data'),
            html.Div(id='Continuous-options'),
        ]),
        
        dcc.Tab(label='Production', children=[
            html.H2(children='Production'),
            html.Label('How much Area do you have available to install PV panels?'),
            html.Label('Area'),
            dcc.Input(
                id='area-input',
                type='number',
                placeholder='Enter area...',
                min=0
            ),
            html.Button('Lock In', id='lock-button'),
            html.Div(id='lock-message'),
            html.Div(id='production-results')
        ])
        
        
        
        
        
        
    ])
])


@app.callback(
    [Output('kw-value', 'children'),
     Output('sum-of-powers', 'children')],
    [Input('Irrigation', 'value'),
     Input('Continuous_Machine', 'value'),
     Input('Seasonal_Machine','value'),
     Input('hectares', 'value'),
     Input('hours_per_day', 'value'),
     Input('machine-dropdown', 'value'),
     Input('select-day-dropdown', 'value'),
     Input('hours_per_day_1', 'value'),
     Input('machine-dropdown_Seasonal', 'value'),
     Input('Season','value'),
     Input('select-day-dropdown_seasonal', 'value'),
     Input('hours_per_day_2', 'value'),
     ]
)

def update_outputs(Irrigation_Q, Continuous_Machine, Seasonal_Machine,
                   hectares, hours_per_day,
                   selected_machines, selected_days_of_week, hours_per_day_1,
                   selected_machines_Seasonal, Season, select_days_of_week_season, hours_per_day_2):

    global consumption_graph  # Access the global DataFrame variable

    if Irrigation_Q == 'Yes':
        if hectares and hours_per_day and int(hours_per_day) > 0:
            hectares = int(hectares)
            hours_per_day = int(hours_per_day)

            start_hour = 6  # 6 AM
            end_hour = 19  # 7 PM

            if hours_per_day == 1:
                interval = 1
            else:
                interval = (end_hour - start_hour) // (hours_per_day - 1)

            specific_hours = [start_hour + i * interval for i in range(hours_per_day)]

            Pot = Irrigation['kw'][hectares - 1]

            for index, row in hourly_data.iterrows():
                if row['Date'].hour in specific_hours:
                    hourly_data.at[index, 'Pot'] = Pot

    if Continuous_Machine == 'Yes':
        if selected_machines and selected_days_of_week and int(hours_per_day_1) > 0:
            hours_per_day = int(hours_per_day_1)

            start_hour = 6  # 6 AM
            end_hour = 19  # 7 PM

            if hours_per_day == 1:
                interval = 1
            else:
                interval = (end_hour - start_hour) // (hours_per_day - 1)

            specific_hours_1 = [start_hour + i * interval for i in range(hours_per_day)]

            selected_rows = Machines_list[Machines_list['Machines'].isin(selected_machines)]
            sum_of_powers = selected_rows['kw'].sum()

            for index, row in hourly_data.iterrows():
                if row['Date'].hour in specific_hours_1 and row['Day of Week'] in selected_days_of_week:
                    hourly_data.at[index, 'Continuous_machines'] = sum_of_powers

    if Seasonal_Machine == 'Yes':
        if selected_machines_Seasonal and select_days_of_week_season and int(hours_per_day_2) > 0:
            hours_per_day = int(hours_per_day_2)

            start_hour = 6  # 6 AM
            end_hour = 19  # 7 PM

            if hours_per_day == 1:
                interval = 1
            else:
                interval = (end_hour - start_hour) // (hours_per_day - 1)

            specific_hours_1 = [start_hour + i * interval for i in range(hours_per_day)]

            selected_rows = Machines_list[Machines_list['Machines'].isin(selected_machines)]

            sum_of_powers = selected_rows['kw'].sum()

            for index, row in hourly_data.iterrows():
                if row['Date'].hour in specific_hours_1 and row['Day of Week'] in select_days_of_week_season and row['Season Number'] == Season:
                    hourly_data.at[index, 'Seasonal_machines'] = sum_of_powers

    if Continuous_Machine == 'No':
        hourly_data['Continuous_machines'] = 0

    if Irrigation_Q == 'No':
        hourly_data['Pot'] = 0

    if Seasonal_Machine == 'No':
        hourly_data['Seasonal_machines'] = 0

    hourly_table_data = hourly_data.to_dict('records')
    
    # Create a consumption graph DataFrame
    consumption_graph = hourly_data[['Date', 'Pot', 'Continuous_machines', 'Seasonal_machines']].copy()

    # Generate the graph based on consumption_graph data
    # You can add the graph generation code here

    # Return placeholders for kw-value and sum-of-powers
    return "Placeholder for kw-value", "Placeholder for sum-of-powers"



@app.callback(
    Output('output-data', 'children'),
    [Input('add-column-button', 'n_clicks')],
    [State('District', 'value'),
     State('output-data', 'children')]
)
def add_new_column(n_clicks, district, children):
    global consumption_graph
    global latitude
    global longitude

    if n_clicks is None or n_clicks == 0:
        return children

    # Fetch latitude and longitude based on the selected district
    district_info = Districs[Districs['District'] == district]
    latitude = district_info['Latitude'].values[0]
    longitude = district_info['Longitude'].values[0]

    # Calculate the sum of columns and store it in the consumption_graph DataFrame
    hourly_data['Sum_of_Columns'] = hourly_data[['Consumo registado (kW)', 'Pot', 'Seasonal_machines', 'Continuous_machines']].sum(axis=1)

    # Append the values used in the graph to the consumption_graph DataFrame
    consumption_graph = pd.concat([consumption_graph, hourly_data[['Date', 'Sum_of_Columns']]], ignore_index=True)

    # Create the line graph
    line_graph = go.Figure()
    line_graph.add_trace(go.Scatter(x=hourly_data['Date'], y=hourly_data['Sum_of_Columns'], mode='lines', name='Total Sum'))

    # Set the title and axis labels of the graph
    if district:
        title = f'Farm Demand ({district})'
        line_graph.update_layout(title=title,
                                 xaxis_title='Date',
                                 yaxis_title='Demand KWh')

    # Return the graph component
    return dcc.Graph(id='total-sum-graph', figure=line_graph)


@app.callback(
    Output('production-results', 'children'),
    [Input('lock-button', 'n_clicks')],
    [State('area-input', 'value')]
)
def run_pv_model(n_clicks, area):
    global global_energy_data, consumption_graph, latitude, longitude  # Access the global DataFrame variable

    if n_clicks is None:
        return ''

    # Call the get_pvgis_hourly function to retrieve weather data
    data, meta, inputs = pvlib.iotools.get_pvgis_hourly(latitude=latitude, 
                                           longitude=longitude, 
                                           start=2020, 
                                           end=2020,
                                           raddatabase='PVGIS-SARAH2', 
                                           components=True, 
                                           surface_tilt=0, 
                                           surface_azimuth=180,
                                           outputformat='json', 
                                           usehorizon=True, 
                                           userhorizon=None, 
                                           pvcalculation=False, 
                                           peakpower=None,
                                           pvtechchoice='crystSi', 
                                           mountingplace='free', 
                                           loss=0, 
                                           trackingtype=0, 
                                           optimal_surface_tilt=False,
                                           optimalangles=False, 
                                           url='https://re.jrc.ec.europa.eu/api/v5_2/', 
                                           map_variables=True, 
                                           timeout=30)

    data = data.rename(columns={
        'poa_direct': 'dni',  # Direct Normal Irradiance
        'poa_sky_diffuse': 'dhi',  # Diffuse Horizontal Irradiance
        'poa_ground_diffuse': 'ghi',  # Global Horizontal Irradiance
        'solar_elevation': 'solar_elevation',
        'temp_air': 'temp_air',
        'wind_speed': 'wind_speed'
    })

    # Define module and inverter parameters
    cec_modules = pvlib.pvsystem.retrieve_sam('CECMod')
    cec_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
    module = cec_modules['Sunpower_SPR_X21_460_COM']  # 460W
    inverter = cec_inverters['Yaskawa_Solectria_Solar__PVI_23TL_480']  # 20Kw to 25KW

    # Define number of panels
    Module_area = 2
    N_panels = int(area / Module_area)

    # PVSystem initialization
    system = PVSystem(surface_tilt=surface_tilt, surface_azimuth=surface_azimuth,
                      module_parameters=module, inverter_parameters=inverter,
                      temperature_model_parameters=TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass'],
                      albedo=albedo)

    # ModelChain initialization
    mc = ModelChain(system, location, aoi_model='no_loss', spectral_model='no_loss',
                    temperature_model='sapm', losses_model='no_loss')

    # Run the model with provided weather data
    mc.run_model(data)

    # Ensure all negative energy values are changed to 0
    mc.results.ac = mc.results.ac.clip(lower=0)
    
    mc.results.ac = mc.results.ac * N_panels / 1000

    # Resample the data hourly and extract only the month and day
    hourly_data = mc.results.ac.resample('H').sum()
    #hourly_data.index = hourly_data.index.strftime('%m-%d')

    # Store the filtered data points in the global DataFrame
    filtered_data = hourly_data.reset_index()
    filtered_data.columns = ['Date', 'Energy_kWh']
    
    # Add 3 years to the Date column
    filtered_data['Date'] = filtered_data['Date'] + pd.DateOffset(years=3)
    
    global_energy_data = filtered_data.copy()

    daily_energy_graph = dcc.Graph(
        id='daily-energy-graph',
        figure={
            'data': [{'x': filtered_data['Date'], 'y': filtered_data['Energy_kWh'], 'type': 'line', 'name': 'Energy Output daily'}],
            'layout': {'title': 'Energy Production', 'xaxis': {'title': 'Month-Day'}, 'yaxis': {'title': 'Energy kWh'}}
            }
        )

    # Convert the 'Date' column of consumption_graph to regular datetime format without timezone
    consumption_graph['Date'] = consumption_graph['Date'].dt.tz_localize(None)
    
    # Remove timezone information from the datetime column
    global_energy_data['Date'] = global_energy_data['Date'].dt.tz_localize(None)

    # Merge global_energy_data and consumption_graph on the 'Date' column
    merged_data = pd.merge(global_energy_data, consumption_graph, on='Date', how='inner')

    # Plotly graph for merged data
    merged_graph = go.Figure()
    merged_graph.add_trace(go.Scatter(x=merged_data['Date'], y=merged_data['Energy_kWh'], mode='lines', name='Energy Produced'))
    merged_graph.add_trace(go.Scatter(x=merged_data['Date'], y=merged_data['Sum_of_Columns'], mode='lines', name='Energy Consumed'))
    merged_graph.update_layout(title='Energy Production vs. Consumption', xaxis_title='Month-Day', yaxis_title='Energy kWh')

    # Calculate Energy Saved for each point
    merged_data['Energy_Saved'] = merged_data.apply(lambda row: row['Sum_of_Columns'] if row['Energy_kWh'] > row['Sum_of_Columns'] else row['Energy_kWh'], axis=1)

    # Calculate Money Saved for each point
    energy_price = 0.5  # Energy price per kWh
    merged_data['Money_Saved'] = merged_data['Energy_Saved'] * energy_price

    # Create a new DataFrame with the desired columns
    summary_data = merged_data[['Date', 'Energy_kWh', 'Sum_of_Columns', 'Money_Saved', 'Energy_Saved']]

    # Rename the columns for clarity
    summary_data.columns = ['Date', 'Energy_Produced', 'Energy_Consumed', 'Money_Saved', 'Energy_Saved']

    # Calculate total Money Saved throughout the year
    total_money_saved = summary_data['Money_Saved'].sum()

    # HTML element to display total Money Saved
    money_saved_html = html.Div(f"If you installed solar panels in your area you would have saved {total_money_saved:.2f}€!")

    return html.Div([daily_energy_graph, dcc.Graph(id='merged-graph', figure=merged_graph), money_saved_html])



if __name__ == '__main__':
    app.run_server(debug=False)

