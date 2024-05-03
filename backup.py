import pandas as pd
import dash
from dash import dcc, html,Input, Output, State
import plotly.graph_objs as go
import dash_table
from dash import callback_context

Demand_house = pd.read_csv('Janeiro.csv')
Machines_list = pd.read_csv('maquinas.csv')
Irrigation = pd.read_csv('bombas de irrigação.csv')
days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
df_days_of_week = pd.DataFrame(days_of_week, columns=['Day'])

Demand_house['Datetime'] = pd.to_datetime(Demand_house['Data'] + ' ' + Demand_house['Hora'])
hourly_data = Demand_house.groupby(Demand_house['Datetime'].dt.floor('H')).agg({'Consumo registado (kW)': 'sum'})
hourly_data.reset_index(inplace=True)
hourly_data.iloc[0, 0] = hourly_data.iloc[0, 0].strftime('%d-%m-%Y %H')
hourly_data['Day of Week'] = hourly_data['Datetime'].dt.day_name()
hourly_data['Month'] = hourly_data['Datetime'].dt.month
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

# Layout definition
app.layout = html.Div(style={'backgroundColor': 'rgba(144, 238, 144, 0.5)'}, children=[
    html.Div(
        [
            html.H1(children='Amarna', style={'text-align': 'center'}),  # Center-align the header
            html.Div(children='''Minimun Value Product''', style={'text-align': 'center'}),  # Center-align the subheader
        ],
        style={'margin': 'auto', 'width': '50%'}  # Center the entire div horizontally
    ),
    dcc.Tabs([
        dcc.Tab(label='Input', children=[
            html.H2(children='Here we collect the most important information of the client about his demand so that we can create an estimation of the impact it would have if him had our service'),

            html.Label('What district are you in?'),
            dcc.Dropdown(
                id='District',
                options=[{'label': district, 'value': district} for district in Districs['District']],
                value=None,  # Default value is None, user has to select a district
                style={'backgroundColor': 'rgba(144, 238, 144, 0.5)'}  # Set dropdown background color
            ),

            html.Br(),  # Add a line break for better separation

            html.H3(children='Irrigation', style={'font-weight': 'bold', 'backgroundColor': 'rgba(144, 238, 144, 0.5)'}),  # Emphasize Irrigation section with bold text and light green background

            html.Label('Irrigation'),
            dcc.Dropdown(
                id='Irrigation',
                options=[
                    {'label': 'No', 'value': 'No'},
                    {'label': 'Yes', 'value': 'Yes'}
                ],
                value='No',
                style={'backgroundColor': 'rgba(144, 238, 144, 0.5)'}  # Set dropdown background color
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
                value='1',
                style={'backgroundColor': 'rgba(144, 238, 144, 0.5)'}  # Set dropdown background color
            ),
            html.Label('Number of hours per day for irrigation (usually 1-5):'),
            dcc.Input(
                id='hours_per_day',
                type='number',
                placeholder='Enter hours per day',
                value=0
            ),
            html.Div(id='kw-value'),  # Placeholder for kw value initially hidden

            html.Br(),  # Add a line break for better separation

            html.H3(children='Continuous Machines', style={'font-weight': 'bold', 'backgroundColor': 'rgba(144, 238, 144, 0.5)'}),  # Emphasize Continuous Machines section with bold text and light green background

            # Continuos Machine
            html.Label('Continuous_Machine'),
            dcc.Dropdown(
                id='Continuous_Machine',  # Corrected ID
                options=[
                    {'label': 'No', 'value': 'No'},
                    {'label': 'Yes', 'value': 'Yes'}
                ],
                value='No',
                style={'backgroundColor': 'rgba(144, 238, 144, 0.5)'}  # Set dropdown background color
            ),
            html.Label('Enter the machines:'),
            dcc.Dropdown(
                id='machine-dropdown',
                options=[{'label': row[0], 'value': row[0]} for row in Machines_list.values],
                value=[Machines_list.values[0][0]],  # Set default value to the first machine
                multi=True,
                style={'backgroundColor': 'rgba(144, 238, 144, 0.5)'}  # Set dropdown background color
            ),
            html.Label('Select day(s) of the week:'),
            dcc.Dropdown(
                id='select-day-dropdown',
                options=[{'label': day, 'value': day} for day in df_days_of_week['Day']],
                value=[df_days_of_week.iloc[0, 0]],  # Set default value to the first day of the week
                multi=True,
                style={'backgroundColor': 'rgba(144, 238, 144, 0.5)'}  # Set dropdown background color
            ),
            html.Label('How many hours per day :'),
            dcc.Input(
                id='hours_per_day_1',
                type='number',
                placeholder='Enter hours per day',
                value=0
            ),

            html.Br(),  # Add a line break for better separation

            html.H3(children='Seasonal Machines', style={'font-weight': 'bold', 'backgroundColor': 'rgba(144, 238, 144, 0.5)'}),  # Emphasize Seasonal Machines section with bold text and light green background

            # Seasonal Machine
            html.Label('Seasonal_Machine'),
            dcc.Dropdown(
                id='Seasonal_Machine',
                options=[
                    {'label': 'No', 'value': 'No'},
                    {'label': 'Yes', 'value': 'Yes'}
                ],
                value='No',
                style={'backgroundColor': 'rgba(144, 238, 144, 0.5)'}  # Set dropdown background color
            ),
            html.Label('Enter the machines:'),
            dcc.Dropdown(
                id='machine-dropdown_Seasonal',
                options=[{'label': row[0], 'value': row[0]} for row in Machines_list.values],
                value=[Machines_list.values[0][0]],  # Set default value to the first machine
                multi=True,
                style={'backgroundColor': 'rgba(144, 238, 144, 0.5)'}  # Set dropdown background color
            ),
            html.Label('season that you work most: (1 to 4):'),
            dcc.Input(
                id='Season',
                type='number',
                placeholder='Enter hours per day',
                value=0
            ),
            html.Label('Select day(s) of the week:'),
            dcc.Dropdown(
                id='select-day-dropdown_seasonal',
                options=[{'label': day, 'value': day} for day in df_days_of_week['Day']],
                value=[df_days_of_week.iloc[0, 0]],  # Set default value to the first day of the week
                multi=True,
                style={'backgroundColor': 'rgba(144, 238, 144, 0.5)'}  # Set dropdown background color
            ),
            html.Label('How many hours per day :'),
            dcc.Input(
                id='hours_per_day_2',
                type='number',
                placeholder='Enter hours per day',
                value=0
            ),

            html.Button("Click to start", id="add-column-button"),  # Add button to trigger column addition
            html.Div(id='output-data'),  # Placeholder for displaying the new table
            html.Div(id='Continuous-options'),  # Corrected ID
            html.Div(id='sum-of-powers'),
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

def update_outputs(Irrigation_Q, Continuous_Machine,Seasonal_Machine,
                   hectares, hours_per_day,
                   selected_machines, selected_days_of_week,hours_per_day_1,
                   selected_machines_Seasonal,Season,select_days_of_week_season,hours_per_day_2):

    if Irrigation_Q == 'Yes':
        if hectares and hours_per_day and int(hours_per_day) > 0:
            print('3')
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

                if row['Datetime'].hour in specific_hours:

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


            print('1')
            print(selected_machines)
            print (Machines_list['Machines'])
            selected_rows = Machines_list[Machines_list['Machines'].isin(selected_machines)]
            print('2')
            sum_of_powers = selected_rows['kw'].sum()
            print('3')

            for index, row in hourly_data.iterrows():
                if row['Datetime'].hour in specific_hours_1 and row['Day of Week'] in selected_days_of_week:
                    hourly_data.at[index, 'Continuous_machines'] = sum_of_powers
            print('4')

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
                if row['Datetime'].hour in specific_hours_1 and row['Day of Week'] in select_days_of_week_season and row['Season Number'] == Season:
                    hourly_data.at[index, 'Seasonal_machines'] = sum_of_powers


    if Continuous_Machine == 'No':
        hourly_data['Continuous_machines'] = 0


    if Irrigation_Q == 'No':
        hourly_data['Pot'] = 0

    if Seasonal_Machine== 'No':
        hourly_data['Seasonal_machines']=0


    hourly_table_data = hourly_data.to_dict('records')

    return "Placeholder for kw-value", "Placeholder for sum-of-powers"


@app.callback(
    Output('output-data', 'children'),
    [Input('add-column-button', 'n_clicks')],
    [State('District', 'value'),
     State('output-data', 'children')]
)
def add_new_column(n_clicks, district, children):

    if n_clicks is None or n_clicks == 0:
        return children

    print ('0')
    print( Districs['District'])
    print('9')
    print(Districs.info())
    print('8')
    print(Districs)
    district_info = Districs[Districs['District'] == district]

    latitude = district_info['Latitude'].values[0]
    longitude = district_info['Longitude'].values[0]
    print(f'Latitude: {latitude}, Longitude: {longitude}')

    hourly_data['Sum_of_Columns'] = hourly_data[['Consumo registado (kW)', 'Pot', 'Seasonal_machines', 'Continuous_machines']].sum(axis=1)

    # Create a line graph to display the total sum over time
    line_graph = go.Figure()
    line_graph.add_trace(go.Scatter(x=hourly_data['Datetime'], y=hourly_data['Sum_of_Columns'], mode='lines', name='Total Sum'))

    # Include the selected district in the title if the button was clicked
    if district:
        title = f'Farm Demand ({district})'
        line_graph.update_layout(title=title,
                                 xaxis_title='Datetime',
                                 yaxis_title='Demand KWh')

    return dcc.Graph(id='total-sum-graph', figure=line_graph)


if __name__ == '__main__':
    app.run_server(debug=True)