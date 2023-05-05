# EPEX Spot

This component adds electricity prices from stock exchange [EPEX Spot](https://www.epexspot.com) to Home Assistant. [EPEX Spot](https://www.epexspot.com) does not provide free access to the data, so this component uses different ways to retrieve the data.

You can choose between multiple sources:

1. Awattar

   [Awattar](https://www.awattar.de/services/api) provides a free of charge service for their customers. Market price data is available for Germany and Austria. So far no user identifiation is required.

2. EPEX Spot Web Scraper

    This source uses web scraping technologies to retrieve publicly available data from its [website](https://www.epexspot.com/en/market-data).

If you like this component, please give it a star on [github](https://github.com/mampfes/hacs_epex_spot_awattar).

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

1. Current market price
2. Average market price during the day
3. Lowest market price during the day
4. Highest market price during the day
5. Current market price quantile during the day
6. Rank of the current market price during the day

The *EPEX Spot Web Scraper* provides some additional sensors:

- Buy Volume
- Sell Volume
- Volume

### 1. Current Market Price Sensor

The sensor value reports the current market price which will be updated every hour.

The sensor attributes contains a list of all available market prices (today and tomorrow if available):

```yaml
data:
  - start_time: '2022-12-15T23:00:00+00:00'
    end_time: '2022-12-16T00:00:00+00:00'
    price_eur_per_mwh: 296.3
    price_ct_per_kwh: 29.63
  - start_time: '2022-12-16T00:00:00+00:00'
    end_time: '2022-12-16T01:00:00+00:00'
    price_eur_per_mwh: 288.12
    price_ct_per_kwh: 28.812
  - start_time: '2022-12-16T01:00:00+00:00'
    end_time: '2022-12-16T02:00:00+00:00'
    price_eur_per_mwh: 280.19
    price_ct_per_kwh: 28.019
```

### 2. Average Market Price Sensor

The sensor value reports the average market price during the day.

### 3. Lowest Market Price Sensor

The sensor value reports the lowest market price during the day.

The sensor attributes contains the start and endtime of the lowest market price timeframe.

```yaml
start_time: '2023-02-15T22:00:00+00:00'
end_time: '2023-02-15T23:00:00+00:00'
```

### 4. Highest Market Price Sensor

The sensor value reports the highest market price during the day.

The sensor attributes contains the start and endtime of the highest market price timeframe.

```yaml
start_time: '2023-02-15T22:00:00+00:00'
end_time: '2023-02-15T23:00:00+00:00'
```

### 5. Quantile Sensor

The sensor value reports the quantile between the lowest market price and the highest market price during the day in the range between 0 .. 1.

Examples:

- The sensor reports 0 if the current market price is the lowest during the day.
- The sensor reports 1 if the current market price is the highest during the day.
- If the sensor reports e.g., 0.25, then the current market price is 25% of the range between the lowest and the highest market price.

### 6. Rank Sensor

The sensor value reports the rank of the current market price during the day. Or in other words: The number of hours in which the price is lower than the current price.

Examples:

- The sensor reports 0 if the current market price is the lowest during the day. There is no lower market price during the day.
- The sensor reports 23 if the current market price is the highest during the day (if the market price will be updated hourly). There are 23 hours which are cheaper than the current hour market price.
- The sensor reports 1 if the current market price is the 2nd cheapest during the day. There is 1 one which is cheaper than the current hour market price.

## FAQ

### 1. How can I show the prices in ct/KWh?

Since version 1.1.0, every sensor that shows price information has an extra attribute `price_ct_per_kwh`. This can be used for Lovelace cards like the [Entity Card](https://www.home-assistant.io/dashboards/entity/#attribute), automations and visualizations like [ApexCharts](https://github.com/RomRider/apexcharts-card).

Before version 1.1.0, you can use a template sensor like this:

```yaml
template:
  - sensor:
    - name: epex_spot_price_ct_per_kwh
      unit_of_measurement: "ct/KWh"
      availability: '{{ states("sensor.epex_spot_de_price") != "unavailable" }}'
      state: '{{ states("sensor.epex_spot_de_price") | float / 10 }}'
```

Don't forget to replace `de` epex_spot_**de**_price if necessary!

### 2. How can I show a chart of the next hours?

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

### 3. How can I determine the best moment to start appliances?

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

### 4. I want to combine and view everything

Here's an other [ApexCharts](https://github.com/RomRider/apexcharts-card) example.
It shows the price for the current day, the next day and the `min/max` value for each day.
Furthermore, it also fills the hours during which prices are lowest (see 3.)

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
        color: '#186ddc'
      - value: 0.155
        color: '#04822e'
      - value: 0.2
        color: '#12A141'
      - value: 0.25
        color: '#79B92C'
      - value: 0.3
        color: '#C4D81D'
      - value: 0.35
        color: '#F3DC0C'
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
        color: '#186ddc'
      - value: 0.155
        color: '#04822e'
      - value: 0.2
        color: '#12A141'
      - value: 0.25
        color: '#79B92C'
      - value: 0.3
        color: '#C4D81D'
      - value: 0.35
        color: '#F3DC0C'
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
    min: 0.1
    max: 0.5
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
