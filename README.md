# EPEX Spot

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

This component adds electricity prices from stock exchange [EPEX Spot](https://www.epexspot.com) to Home Assistant. [EPEX Spot](https://www.epexspot.com) does not provide free access to the data, so this component uses different ways to retrieve the data.

---

January 2024: Hi there, I'm eperimenting with a new feature:

https://github.com/mampfes/ha_epex_spot_sensor

Please let me know if this is a useful addition to EPEX Spit.

---

You can choose between multiple sources:

1. Awattar

   [Awattar](https://www.awattar.de/services/api) provides a free of charge service for their customers. Market price data is available for Germany and Austria. So far no user identifiation is required.

2. EPEX Spot Web Scraper

   This source uses web scraping technologies to retrieve publicly available data from its [website](https://www.epexspot.com/en/market-data).

3. SMARD.de

   [SMARD.de](https://www.smard.de) provides a free of charge API to retrieve a lot of information about electricity market including market prices. SMARD.de is serviced by the Bundesnetzagentur, Germany.

4. smartENERGY.at

   [smartENERGY.at](https://www.smartenergy.at/api-schnittstellen) provides a free of charge service for their customers. Market price data is available for Austria. So far no user identifiation is required.

If you like this component, please give it a star on [github](https://github.com/mampfes/hacs_epex_spot).

## Installation

1. Ensure that [HACS](https://hacs.xyz) is installed.
2. Install **EPEX Spot** integration via HACS:

   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mampfes&repository=ha_epex_spot)

3. Add **EPEX Spot** integration to Home Assistant:

   [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=epex_spot)

In case you would like to install manually:

1. Copy the folder `custom_components/epex_spot` to `custom_components` in your Home Assistant `config` folder.
2. Add **EPEX Spot** integration to Home Assistant:

   [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=epex_spot)

## Sensors

This integration provides the following sensors:

1. Net market price
2. Market price
3. Average market price during the day
4. Median market price during the day
5. Lowest market price during the day
6. Highest market price during the day
7. Current market price quantile during the day
8. Rank of the current market price during the day

The _EPEX Spot Web Scraper_ provides some additional sensors:

- Buy Volume
- Sell Volume
- Volume

NOTE: For GB data, the prices will be shown in GBP instead of EUR. The sensor attribute names are adjusted accordingly.

### 1. Net Market Price Sensor

The sensor value reports the net market price in ct/kWh. The price value will be updated every hour to reflect the current net market price.

The sensor attributes contains a list of all available net market prices (for today and tomorrow if available) in ct/kWh.

```yaml
data:
  - start_time: "2022-12-15T23:00:00+00:00"
    end_time: "2022-12-16T00:00:00+00:00"
    price_ct_per_kwh: 29.63
  - start_time: "2022-12-16T00:00:00+00:00"
    end_time: "2022-12-16T01:00:00+00:00"
    price_ct_per_kwh: 28.812
  - start_time: "2022-12-16T01:00:00+00:00"
    end_time: "2022-12-16T02:00:00+00:00"
    price_ct_per_kwh: 28.019
```

The net market price will be calculated as follows:

`<Net Price>` = `<Market Price>` + `<Surcharges>` + `<Tax>`

The values for surcharges and tax can be adjusted in the integration configuration. 2 different types of surcharges can be adjusted:

1. Percentage Surcharge, stated in % of the EPEX Spot market price.
2. Absolute Surcharge, stated in ct/kWh.

Example:

```text
Percentage Surchage = 3%
Absolute Surcharge = 12ct
Tax = 19%

Net Price = ((Market Price * 1.03) + 12ct) * 1.19
```

### 2. Market Price Sensor

The sensor value reports the EPEX Spot market price in EUR/MWh. The price value will be updated every hour to reflect the current market price.

The sensor attributes contains additional values:

- The market price in ct/kWh.
- A list of all available market prices (for today and tomorrow if available) in EUR/MWh and ct/kWh.

```yaml
price_ct_per_kwh: 29.63
data:
  - start_time: "2022-12-15T23:00:00+00:00"
    end_time: "2022-12-16T00:00:00+00:00"
    price_eur_per_mwh: 296.3
    price_ct_per_kwh: 29.63
  - start_time: "2022-12-16T00:00:00+00:00"
    end_time: "2022-12-16T01:00:00+00:00"
    price_eur_per_mwh: 288.12
    price_ct_per_kwh: 28.812
  - start_time: "2022-12-16T01:00:00+00:00"
    end_time: "2022-12-16T02:00:00+00:00"
    price_eur_per_mwh: 280.19
    price_ct_per_kwh: 28.019
```

### 3. Average Market Price Sensor

The sensor value reports the average EPEX Spot market price during the day. The sensor value reports the market price in EUR/MWh. The market price in ct/kWh is available as sensor attribute.

```yaml
price_ct_per_kwh: 29.63
```

### 4. Median Market Price Sensor

The sensor value reports the median EPEX Spot market price during the day. The sensor value reports the market price in EUR/MWh. The market price in ct/kWh is available as sensor attribute.

```yaml
price_ct_per_kwh: 29.63
```

### 5. Lowest Market Price Sensor

The sensor value reports the lowest EPEX Spot market price during the day. The sensor value reports the market price in EUR/MWh. The market price in ct/kWh is available as sensor attribute.

The sensor attributes contains the start and endtime of the lowest market price timeframe.

```yaml
price_ct_per_kwh: 29.63
start_time: "2023-02-15T22:00:00+00:00"
end_time: "2023-02-15T23:00:00+00:00"
```

### 6. Highest Market Price Sensor

The sensor value reports the highest EPEX Spot market price during the day. The sensor value reports the market price in EUR/MWh. The market price in ct/kWh is available as sensor attribute.

The sensor attributes contains the start and endtime of the highest market price timeframe.

```yaml
price_ct_per_kwh: 29.63
start_time: "2023-02-15T22:00:00+00:00"
end_time: "2023-02-15T23:00:00+00:00"
```

### 7. Quantile Sensor

The sensor value reports the quantile between the lowest market price and the highest market price during the day in the range between 0 .. 1.

Examples:

- The sensor reports 0 if the current market price is the lowest during the day.
- The sensor reports 1 if the current market price is the highest during the day.
- If the sensor reports e.g., 0.25, then the current market price is 25% of the range between the lowest and the highest market price.

### 8. Rank Sensor

The sensor value reports the rank of the current market price during the day. Or in other words: The number of hours in which the price is lower than the current price.

Examples:

- The sensor reports 0 if the current market price is the lowest during the day. There is no lower market price during the day.
- The sensor reports 23 if the current market price is the highest during the day (if the market price will be updated hourly). There are 23 hours which are cheaper than the current hour market price.
- The sensor reports 1 if the current market price is the 2nd cheapest during the day. There is 1 one which is cheaper than the current hour market price.

## Service Calls

List of Service Calls:

- Get Lowest Price Interval
- Get Highest Price Interval
- Fetch Data

### 1. Get Lowest and Highest Price Interval

**Requires Release >= 2.0.0**

Get the time interval during which the price is at its lowest/highest point.

Knowing the hours with the lowest / highest consecutive prices during the day could be an interesting use case. This might be of value when looking for the most optimum time to start your washing machine, dishwasher, dryer, etc.

With this service call, you can let the integration calculate the optimal start time. The only mandatory attribute is the duration of your appliance. Optionally you can limit start- and end-time, e.g. to start your appliance only during night hours.

```yaml
epex_spot.get_lowest_price_interval
epex_spot.get_highest_price_interval
```

| Service data attribute | Optional | Description                                                                     | Example                          |
| ---------------------- | -------- | ------------------------------------------------------------------------------- | -------------------------------- |
| `device_id`            | yes      | A EPEX Spot service instance ID. In case you have multiple EPEX Spot instances. | 9d44d8ce9b19e0863cf574c2763749ac |
| `earliest_start`       | yes      | Earliest time to start the appliance.                                           | "14:00:00"                       |
| `earliest_start_post`  | yes      | Postponement of `earliest_start` in days: 0 = today (default), 1= tomorrow      | 0                                |
| `latest_end`           | yes      | Latest time to end the appliance.                                               | "16:00:00"                       |
| `latest_end_post`      | yes      | Postponement of `latest_end` in days: 0 = today (default), 1= tomorrow          | 0                                |
| `duration`             | no       | Required duration to complete appliance.                                        | See below...                     |

Notes:

- If `earliest_start` is omitted, the current time is used instead.
- If `latest_end` is omitted, the end of all available market data is used.
- `earliest_start` refers to today if `earliest_start_post` is omitted or set to 0.
- `latest_end` will be automatically trimmed to the available market area.
- If `earliest_start` and `latest_end` are present _and_ `latest_end` is earlier than (or equal to) `earliest_start`, then `latest_end` refers to tomorrow.
- `device_id` is only required if have have setup multiple EPEX Spot instances. The easiest way to get the unique device id, is to use the _Developer Tools -> Services_.

Service Call Examples:

```yaml
service: epex_spot.get_lowest_price_interval
data:
  device_id: 9d44d8ce9b19e0863cf574c2763749ac
  earliest_start: "14:00:00"
  latest_end: "16:00:00"
  duration:
    hours: 1
    minutes: 0
    seconds: 0
```

```yaml
service: epex_spot.get_lowest_price_interval
data:
  earliest_start: "14:00:00"
  latest_end: "16:00:00"
  duration: "00:30:00" # 30 minutes
```

```yaml
service: epex_spot.get_lowest_price_interval
data:
  duration: "00:30" # 30 minutes
```

```yaml
service: epex_spot.get_lowest_price_interval
data:
  duration: 120 # in seconds -> 2 minutes
```

```yaml
# get the lowest price all day tomorrow:
service: epex_spot.get_lowest_price_interval
data:
  earliest_start: "00:00:00"
  earliest_start_post: 1
  latest_end: "00:00:00"
  latest_end_post: 2
  duration: "01:30:00" # 1h, 30 minutes
```

#### Response

The response contains the calculated start and end-time and the average price per MWh/KWh.

Example:

```yaml
start: "2023-09-29T12:00:00+00:00"
end: "2023-09-29T13:00:00+00:00"
price_eur_per_mwh: 77.04
price_ct_per_kwh: 7.704000000000001
net_price_ct_per_kwh: 23.6394928
```

With Home Assistant release >= 2023.9 you can use the [Template Integration](https://www.home-assistant.io/integrations/template/) to create a sensor that shows the start time:

![Start Appliance Sensor](/images/start_appliance_sensor.png)

```yaml
template:
  - trigger:
      - platform: time
        at: "00:00:00"
    action:
      - service: epex_spot.get_lowest_price_interval
        data:
          earliest_start: "20:00:00"
          latest_end: "23:00:00"
          duration:
            hours: 1
            minutes: 5
        response_variable: resp
    sensor:
      - name: Start Appliance
        device_class: timestamp
        state: "{{ resp.start is defined and resp.start }}"
```

This sensor can be used to trigger automations:

```yaml
trigger:
  - platform: time
    at: sensor.start_appliance
condition: []
action: []
```

### 2. Fetch Data

**Requires Release >= 2.1.0**

Fetch data from all services or a specific service.

```yaml
epex_spot.fetch_data
```

| Service data attribute | Optional | Description                                                                     | Example                          |
| ---------------------- | -------- | ------------------------------------------------------------------------------- | -------------------------------- |
| `device_id`            | yes      | A EPEX Spot service instance ID. In case you have multiple EPEX Spot instances. | 9d44d8ce9b19e0863cf574c2763749ac |

## FAQ

### 1. How can I show a chart of the next hours?

With [ApexCharts](https://github.com/RomRider/apexcharts-card), you can easily show a chart like this:

![apexchart](/images/apexcharts.png)

You just have to install [ApexCharts](https://github.com/RomRider/apexcharts-card) (via HACS) and enter the following data in the card configuration:

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Electricity Prices
graph_span: 48h
span:
  start: day
now:
  show: true
  label: Now
series:
  - entity: sensor.epex_spot_de_price
    name: Electricity Price
    type: column
    extend_to: end
    data_generator: >
      return entity.attributes.data.map((entry, index) => { return [new
      Date(entry.start_time).getTime(), entry.price_eur_per_mwh]; });
```

### 2. How can I determine the best moment to start appliances?

**NOTE: Deprecated since release 2.0.0. Use Service call instead!**

It might be an interesting use case to know what the hours with lowest consecutive prices during the day are. This might be of value when looking for the most optimum time to start your washing machine, dishwasher, dryer, etc.
The template below determines when the 3 hours with lowest consecutive prices start, between 06:00 and 22:00.
You can change these hours in the template below, if you want hours before 06:00 and after 22:00 also to be considered.
Remove `{%- set ns.combo = ns.combo[6:22] %}` do disable this filtering completely.

```yaml
template:
  - sensor:
      - name: epex_start_low_period
        state: >-
          {% set ns = namespace(attr_dict=[]) %}
          {% for item in (state_attr('sensor.epex_spot_be_price', 'data'))[0:24] %}
              {%- set ns.attr_dict = ns.attr_dict + [(loop.index-1,item["price_eur_per_mwh"])] %}
          {% endfor %}
          {%- set price_map = dict(ns.attr_dict) %}
          {%- set price_sort = price_map.values()|list %}
          {%- set keys_list = price_map.keys()|list %}
          {%- set ns = namespace(combo=[]) %}
          {%- for p in keys_list %}
            {%- set p = p|int %}
            {%- if p < 22 %}
              {%- set ns.combo = ns.combo + [(p, ((price_sort)[p] + (price_sort)[p+1] + (price_sort)[p+2])|round(2))] %}
            {%- endif %}
          {%- endfor %}
          {%- set ns.combo = ns.combo[6:22] %}
          {%- set mapper = dict(ns.combo) %}
          {%- set key = mapper.keys()|list %}
          {%- set val = mapper.values()|list %}
          {%- set val_min = mapper.values()|min %}
          {{ key[val.index(val_min)]|string + ":00" }}
```

### 3. I want to combine and view everything

Here's another [ApexCharts](https://github.com/RomRider/apexcharts-card) example.
It shows the price for the current day, the next day and the `min/max` value for each day.
Furthermore, it also fills the hours during which prices are lowest (see 2.)

![apexchart](/images/apex_advanced.png)

```yaml
type: custom:apexcharts-card
header:
  show: false
graph_span: 48h
span:
  start: day
now:
  show: true
  label: Now
color_list:
  - var(--primary-color)
series:
  - entity: sensor.epex_spot_be_price
    yaxis_id: uurprijs
    float_precision: 2
    type: line
    curve: stepline
    extend_to: false
    show:
      extremas: true
    data_generator: >
      return entity.attributes.data.map((entry, index) => { return [new
      Date(entry.start_time).getTime(), entry.price_eur_per_mwh]; }).slice(0,24);
    color_threshold:
      - value: 0
        color: "#186ddc"
      - value: 0.155
        color: "#04822e"
      - value: 0.2
        color: "#12A141"
      - value: 0.25
        color: "#79B92C"
      - value: 0.3
        color: "#C4D81D"
      - value: 0.35
        color: "#F3DC0C"
      - value: 0.4
        color: red
      - value: 0.5
        color: magenta
  - entity: sensor.epex_spot_be_price
    yaxis_id: uurprijs
    float_precision: 2
    type: line
    curve: stepline
    extend_to: end
    show:
      extremas: true
    data_generator: >
      return entity.attributes.data.map((entry, index) => { return [new
      Date(entry.start_time).getTime(), entry.price_eur_per_mwh]; }).slice(23,47);
    color_threshold:
      - value: 0
        color: "#186ddc"
      - value: 0.155
        color: "#04822e"
      - value: 0.2
        color: "#12A141"
      - value: 0.25
        color: "#79B92C"
      - value: 0.3
        color: "#C4D81D"
      - value: 0.35
        color: "#F3DC0C"
      - value: 0.4
        color: red
      - value: 0.5
        color: magenta
  - entity: sensor.epex_spot_be_price
    yaxis_id: uurprijs
    color: green
    float_precision: 2
    type: area
    curve: stepline
    extend_to: false
    data_generator: >
      return entity.attributes.data.map((entry, index) => { return [new
      Date(entry.start_time).getTime(), entry.price_eur_per_mwh];}).slice(parseInt(hass.states['sensor.epex_start_low_period'].state.substring(0,2)),parseInt(hass.states['sensor.epex_start_low_period'].state.substring(0,2))+4);

experimental:
  color_threshold: true
yaxis:
  - id: uurprijs
    decimals: 2
    apex_config:
      title:
        text: €/MWh
      tickAmount: 4
apex_config:
  legend:
    show: false
  tooltip:
    x:
      show: true
      format: HH:00 - HH:59
```
