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
2. Install **EPEX Spot** integration via HACS.
3. Add **EPEX Spot** integration to Home Assistant:

   [![badge](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=epex_spot)

In case you would like to install manually:

1. Copy the folder `custom_components/epex_spot` to `custom_components` in your Home Assistant `config` folder.
2. Add **EPEX Spot** integration to Home Assistant:

    [![badge](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=epex_spot)

## Sensors

This component provides one sensor for market prices. The sensor state is the current price in EUR/MWh.

Some sources (like EPEX Spot Web Scraper) provide additional sensors like buy volume, sell volume or volume.

### Sensor Attributes

In addition to the current market price, the price sensor also provides a list of upcoming prices per hour:

```yaml
unit_of_measurement: EUR/MWh
icon: mdi:currency-eur
friendly_name: EPEX Spot DE-LU Price
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
