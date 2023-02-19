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
  - start_time: '2022-12-16T00:00:00+00:00'
    end_time: '2022-12-16T01:00:00+00:00'
    price_eur_per_mwh: 288.12
  - start_time: '2022-12-16T01:00:00+00:00'
    end_time: '2022-12-16T02:00:00+00:00'
    price_eur_per_mwh: 280.19
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

### 1. How can I show the prices in ct/kWh?

Add a template sensor like this:

```yaml
template:
  - sensor:
    - name: epex_spot_price_ct_per_kWh
      unit_of_measurement: "ct/kWh"
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
