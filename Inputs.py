import pandas as pd
import matplotlib.pyplot as plt

Demand_house = pd.read_csv('Janeiro.csv')
Machines_list=pd.read_csv('maquinas.csv')

# Convert 'Data' and 'Hora' columns to datetime
Demand_house['Datetime'] = pd.to_datetime(Demand_house['Data'] + ' ' + Demand_house['Hora'])

# Group by hour, summing the 'Consumo registado (kW)' values
hourly_data = Demand_house.groupby(Demand_house['Datetime'].dt.floor('H')).agg({'Consumo registado (kW)': 'sum'})

# Reset index to make 'Datetime' a regular column
hourly_data.reset_index(inplace=True)

# Convert the first datetime value to string format
hourly_data.iloc[0, 0] = hourly_data.iloc[0, 0].strftime('%d-%m-%Y %H')

# Add a column for the day of the week
hourly_data['Day of Week'] = hourly_data['Datetime'].dt.day_name()
hourly_data['Month'] = hourly_data['Datetime'].dt.month
hourly_data['Continuous_machines'] = 0
hourly_data['Seasonal_machines'] = 0
print(hourly_data)
print(hourly_data.info())

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
print(hourly_data)
print(hourly_data.info())

# Read the irrigation data
Irrigation = pd.read_csv('bombas de irrigação.csv')
print(Irrigation)

# Prompt the user to specify the number of hectares and hours per day for irrigation
hectares = int(input("Enter the number of hectares: "))
hours_per_day = int(input("Enter the number of hours per day for irrigation: "))

# Calculate the start and end hours for irrigation (e.g., from 6 AM to 7 PM)
start_hour = 6  # 6 AM
end_hour = 19   # 7 PM
interval = (end_hour - start_hour) // (hours_per_day - 1)
specific_hours = [start_hour + i * interval for i in range(hours_per_day)]

# Print the list of specific hours
print("The hours of the day for irrigation are:", specific_hours)

# Find the corresponding kW value
for index, row in Irrigation.iterrows():
    if row['Min. hect'] <= hectares <= row['Max. hect']:
        Pot = row['kw']
        break

# Create a new column to store the Pot values for specific hours
hourly_data['Pot'] = 0

# Iterate over each row in the hourly_data DataFrame
for index, row in hourly_data.iterrows():
    # Check if the hour corresponds to one of the specific hours
    if row['Datetime'].hour in specific_hours:
        # Assign the Pot value to the corresponding row
        hourly_data.at[index, 'Pot'] = Pot

# Print the hourly_data DataFrame
print(hourly_data)

print(hourly_data[hourly_data['Datetime'].dt.date == pd.Timestamp('2023-02-03').date()])

#continuos machines
selected_machines = []
for i in range(3):
    machine = input("Enter machine {} name: ".format(i+1))
    selected_machines.append(machine)

# Printing all questions answered
print("\nQuestions answered:")
Days_per_week = int(input("How many days of the week: "))

selected_days_of_week = []
for i in range(Days_per_week):
    machine = input("Enter days of the weak {} name: ".format(i+1))
    selected_days_of_week.append(machine)

hours_per_day = int(input("How many hours per day : "))
start_hour = 6  # 6 AM
end_hour = 19   # 7 PM
interval = (end_hour - start_hour) // (hours_per_day - 1)
specific_hours = [start_hour + i * interval for i in range(hours_per_day)]

total = 0
selected_machine_powers = []  # Store machine powers
for machine in selected_machines:
    machine_data = Machines_list[Machines_list['Machines'] == machine]
    if not machine_data.empty:
        machine_kw = machine_data.iloc[0]['kw']
        selected_machine_powers.append(machine_kw)
        print("- {}: {} kW".format(machine, machine_kw))

# Calculate the total power consumption of selected machines
selected_machine_data = Machines_list[Machines_list['Machines'].isin(selected_machines)]
total = selected_machine_data['kw'].sum()

print("\nSelected days of the week:")
for day in selected_days_of_week:
    print("- {}".format(day))

hourly_data['Continuous_machines'] = 0
for index, row in hourly_data.iterrows():
    # Check if the hour corresponds to one of the specific hours
    if row['Datetime'].hour in specific_hours and row['Day of Week'] in selected_days_of_week:
        hourly_data.at[index, 'Continuous_machines'] = total

print(hourly_data[hourly_data['Datetime'].dt.date == pd.Timestamp('2023-02-03').date()][['Datetime', 'Day of Week']])
print(hourly_data[hourly_data['Datetime'].dt.date == pd.Timestamp('2023-02-03').date()])

#seasonal machines

selected_machines = []
for i in range(3):
    machine = input("Enter machine {} name: ".format(i+1))
    selected_machines.append(machine)

# Printing all questions answered
print("\nQuestions answered:")
season_year= int(input('whats the season that you work most: (1 to 4)'))
Days_per_week = int(input("How many days of the week: "))

selected_days_of_week = []
for i in range(Days_per_week):
    machine = input("Enter days of the weak {} name: ".format(i+1))
    selected_days_of_week.append(machine)

hours_per_day = int(input("How many hours per day : "))
start_hour = 6  # 6 AM
end_hour = 19   # 7 PM
interval = (end_hour - start_hour) // (hours_per_day - 1)
specific_hours = [start_hour + i * interval for i in range(hours_per_day)]

total = 0
selected_machine_powers = []
for machine in selected_machines:
    machine_data = Machines_list[Machines_list['Machines'] == machine]
    if not machine_data.empty:
        machine_kw = machine_data.iloc[0]['kw']
        selected_machine_powers.append(machine_kw)
        print("- {}: {} kW".format(machine, machine_kw))

# Calculate the total power consumption of selected machines
selected_machine_data = Machines_list[Machines_list['Machines'].isin(selected_machines)]
total = selected_machine_data['kw'].sum()

print("\nSelected days of the week:")
for day in selected_days_of_week:
    print("- {}".format(day))

hourly_data['Seasonal_machines'] = 0


for index, row in hourly_data.iterrows():
    if row['Datetime'].hour in specific_hours and row['Day of Week'] in selected_days_of_week and row['Season Number'] == season_year:
        hourly_data.at[index, 'Seasonal_machines'] = total

print(hourly_data[hourly_data['Datetime'].dt.date == pd.Timestamp('2023-02-03').date()][['Datetime', 'Day of Week', 'Seasonal_machines']])
print(hourly_data[hourly_data['Datetime'].dt.date == pd.Timestamp('2023-02-03').date()])

hourly_data['total']=hourly_data['Consumo registado (kW)']+ hourly_data['Continuous_machines']+ hourly_data['Seasonal_machines'] +hourly_data['Pot']
print(hourly_data['total'])


plt.plot(hourly_data['Datetime'], hourly_data['total'], color='red', label='Total')

plt.plot(hourly_data['Datetime'], hourly_data['Consumo registado (kW)'], color='blue', label='Consumo registado (kW)')


# Set labels and title
plt.xlabel('Datetime')
plt.ylabel('Power (kW)')
plt.title('Power Consumption')
plt.legend()

# Show plot
plt.show()