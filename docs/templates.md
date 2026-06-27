# Ready-to-Use Energy Provider Price Templates

Below is a list of pre-configured templates for popular dynamic energy providers. You can copy and paste these directly into the **Import price template** and/or **Export price template** field in the integration options.

---

## 🛠️ Available Variables in Templates

When writing or customizing your own templates, the integration exposes the following variables:

* **`market_price`**: The raw EPEX spot market price per kWh as a floating-point number.
* **`now()`**: A localized Home Assistant `datetime` object representing the specific hour/interval block being evaluated. 
  * *Tip:* This allows you to check the current hour (`now().hour`), month (`now().month`), or day of the week (`now().weekday()`) to build time-of-day or seasonal pricing.

---

## 🌍 Quick Navigation

Select your country to jump directly to the configuration templates:

* [🇳🇱 Netherlands (Nederland)](#-netherlands-nederland)
* [🇦🇹 Austria (Österreich)](#-austria-österreich)
* [🇩🇪 Germany (Deutschland)](#-germany-deutschland)

---

## 🇳🇱 Netherlands (Nederland)

### 1. Zonneplan
Zonneplan applies a fixed surcharge per kWh including procurement costs. For export (feeding back to the grid), they offer a **Zonnebonus** (10% extra yield on top of the total price including tax, between sunrise and sunset).
* **Import Template:**
```jinja2
{# Energy tax #}
{% if now().strftime('%Y-%m-%d') >= '2027-01-01' %}
  {# Replace 0.1234 with the actual government energy tax rate for 2027, including VAT #}
  {% set energy_tax = 0.1234 %}
{% else %}
  {# Current 2026 energy tax #}
  {% set energy_tax = 0.110848 %}
{% endif %}

{{ (market_price * 1.21) + 0.02 + energy_tax }}
```

* **Export Template:**
```jinja2
{# Energy tax #}
{% if now().strftime('%Y-%m-%d') >= '2027-01-01' %}
  {# Energy tax return stops from January 1st, 2027 onwards #}
  {% set energy_tax = 0 %}
{% else %}
  {# Current 2026 energy tax #}
  {% set energy_tax = 0.110848 %}
{% endif %}

{% set export_base = (market_price * 1.21) + 0.02 %}
{# Check if the calculated hour falls between sunrise and sunset #}
{% if export_base > 0 and
      now() > today_at(state_attr('sun.sun', 'next_rising') | as_timestamp | timestamp_custom('%H:%M', true)) and 
      now() < today_at(state_attr('sun.sun', 'next_setting') | as_timestamp | timestamp_custom('%H:%M', true)) %}
  {{ (export_base * 1.10) + energy_tax }}
{% else %}
  {{ export_base + energy_tax }}
{% endif %}
```
  
### 2. NextEnergie
Zonneplan applies a fixed surcharge per kWh including procurement costs for import only. For export NextEnergie offers a massive **Zonnebonus** (50% extra yield on top of your export price including tax, between 06:00 and 22:00).
* **Import Template:**
```jinja2
{# Energy tax #}
{% if now().strftime('%Y-%m-%d') >= '2027-01-01' %}
  {# Replace 0.1234 with the actual government energy tax rate for 2027, including VAT #}
  {% set energy_tax = 0.1234 %}
{% else %}
  {# Current 2026 energy tax #}
  {% set energy_tax = 0.110848 %}
{% endif %}

{{ (market_price * 1.21) + 0.0219 + energy_tax }}
```

* **Export Template:**
```jinja2
{# Energy tax #}
{% if now().strftime('%Y-%m-%d') >= '2027-01-01' %}
  {# Energy tax return stops from January 1st, 2027 onwards #}
  {% set energy_tax = 0 %}
{% else %}
  {# Current 2026 energy tax #}
  {% set energy_tax = 0.110848 %}
{% endif %}

{% set export_base = market_price * 1.21 %}
{# Check if the calculated hour is between 06:00 and 22:00 #}
{% if export_base > 0 and now().hour >= 6 and now().hour < 22 %}
  {{ (export_base * 1.50) + energy_tax }}
{% else %}
  {{ export_base + energy_tax }}
{% endif %}
```
  
---

## 🇦🇹 Austria (Österreich)

### Sommer-Nieder-Arbeitspreis (SNAP)

As of April 1, 2026, Austria introduced the **Sommer-Nieder-Arbeitspreis (SNAP)** for grid distribution fees (Netzebene 7 / households). This regulation grants a **20% discount on the grid usage rate** (Netznutzungsentgelt) during the summer half-year (**April 1st to September 30th**) between **10:00 and 16:00** daily.

Below is a template that automatically applies the SNAP discount based on the current month and hour, and adds your fixed charges and VAT.

```jinja2
{# --- CONFIGURATION OF YOUR FIXED RATES (Adjust to your situation) --- #}
{% set base_grid_rate = 0.0700 %} {# Your normal grid usage rate per kWh excluding VAT #}
{% set other_surcharges = 0.1234 %} {# Energy taxes, fixed surcharges, etc. #}
{% set vat = 1.20 %} {# 20% VAT in Austria #}

{# --- SNAP LOGICA (Automatic Calculation) --- #}
{% set is_summer_month = now().month >= 4 and now().month <= 9 %}
{% set is_snap_hour = now().hour >= 10 and now().hour < 16 %}

{% if is_summer_month and is_snap_hour %}
  {# 20% discount on the grid rate during SNAP hours #}
  {% set current_grid_rate = base_grid_rate * 0.80 %}
{% else %}
  {# Regular grid rate outside of SNAP hours #}
  {% set current_grid_rate = base_grid_rate %}
{% endif %}

{# --- FINAL PRICE CALCULATION --- #}
{{ (market_price + current_grid_rate + other_surcharges) * vat }}
```

---

## 🇩🇪 Germany (Deutschland)

### §14a EnWG (Import)

Under **§14a EnWG**, German grid operators (Netzbetreiber) provide time-variable grid fees (HT, ST, NT). 

**Quarterly variation:** Operators can restrict these variable time-windows to specific quarters of the year (e.g., only during high-load winter or high-solar summer quarters). During off-quarters, the Standard Tariff (ST) usually applies 24/7.

>[!NOTE]
>**Price Intervals & Time Restrictions**
>
>If your integration is configured to use a 1-hour price interval, you cannot apply grid fee changes that occur on half-hour or quarter-hour marks (e.g., a tariff switching at 17:30).
>The rate determined at the start of the hour will be calculated for the entire hour. If your local grid operator enforces strict mid-hour tariff shifts, consider switching the integration to a 15-minute price interval sensor (if available for your region) to ensure accurate calculations.

```jinja2
{# --- CONFIGURATION OF YOUR LOCAL GRID FEES --- #}
{% set grid_nt = 0.0250 %} {# Low tariff rate per kWh #}
{% set grid_st = 0.0550 %} {# Standard tariff rate per kWh #}
{% set grid_ht = 0.0850 %} {# High tariff rate per kWh #}

{% set other_surcharges = 0.1420 %} {# Taxes, StromSt, etc. #}
{% set vat = 1.19 %} {# 19% VAT #}

{# --- QUARTERLY & TIME PROFILE LOGIC --- #}
{% set current_month = now().month %}
{% set current_hour = now().hour %}
{% set is_weekend = now().weekday() >= 5 %}

{# Define active quarters (Example: Q1/Jan-Mar and Q4/Oct-Dec are active) #}
{% set is_active_quarter = current_month <= 3 or current_month >= 10 %}

{% if is_active_quarter and not is_weekend %}
  {# Weekday profile during active quarters (Peak morning/evening = HT, Night = NT) #}
  {% if (current_hour >= 8 and current_hour < 12) or (current_hour >= 17 and current_hour < 19) %}
    {% set current_grid_rate = grid_ht %}
  {% elif (current_hour < 3) or (current_hour >= 19) %}
    {% set current_grid_rate = grid_nt %}
  {% else %}
    {% set current_grid_rate = grid_st %}
  {% endif %}
{% else %}
  {# Off-quarters or weekends: Variable fees are disabled, ST applies 24/7 #}
  {# (Note: check if your provider uses NT on weekends during off-quarters) #}
  {% set current_grid_rate = grid_st %}
{% endif %}

{# --- FINAL PRICE CALCULATION --- #}
{{ (market_price + current_grid_rate + other_surcharges) * vat }}
```


### EEG-Feed-in with §51 EEG / Solarspitzengesetz (Export)

For German PV owners utilizing the fixed statutory feed-in tariff (**EEG-Einspeisevergütung**), the rules regarding negative electricity prices became significantly stricter under the **Solarspitzengesetz**. 
For new systems, your statutory feed-in compensation instantly drops to **€0.00** as soon as the EPEX SPOT market price falls below zero. Old systems retain their historical protection rules (*Bestandsschutz*).

```jinja2
{% if market_price <= 0 %}
  {# If the EPEX market price drops below or equals 0, the statutory subsidy is voided #}
  0.0000
{% else %}
  {# As long as the market price is positive, you receive your fixed tariff #}
  0.0750
{% endif %}
```

---

## 🌍 Other Countries
*Templates for other countries will be added here. Feel free to open a Pull Request to submit yours!*