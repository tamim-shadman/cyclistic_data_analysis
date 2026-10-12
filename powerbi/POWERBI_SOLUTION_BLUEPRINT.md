# Cyclistic Bike-Share Analytics — Power BI Dashboard Blueprint

This document provides a visual-by-visual build guide for constructing the **Cyclistic Executive Power BI Report**. It specifies every card, chart, table, and slicer across all 5 report pages.

---

## 📑 Page 1: Executive Ridership & KPI Cockpit

**Page Purpose:** Provides the Chief Commercial Officer and Executive Leadership with a 30-second pulse on ridership volume, member-versus-casual share, vehicle preference, and top network stations.

### Visual Layout & Configuration

```
+----------------------------------------------------------------------------------------------------+
|  SLICER BAR: [Date Range / Year] | [User Type] | [Day Type (Wkday/Wkend)] | [Bike Type]            |
+--------------------+--------------------+--------------------+--------------------+----------------+
|  KPI 1: TOTAL      |  KPI 2: MEMBER     |  KPI 3: CASUAL     |  KPI 4: AVG RIDE   |  KPI 5: PRIME  |
|  RIDES             |  SHARE %           |  SHARE %           |  DURATION (MIN)    |  CONVERSION    |
|  61,973            |  55.2%             |  44.8%             |  19.8 min          |  11,480        |
+--------------------+--------------------+--------------------+--------------------+----------------+
|  VISUAL 1: (Width: 65%)                                      |  VISUAL 2: (Width: 35%)             |
|  Daily Ridership Volume & 7-Day Moving Average               |  Rider Split by Membership (Donut)  |
|  Line Chart with Trendline & Zoom Slider                     |                                     |
+--------------------------------------------------------------+-------------------------------------+
|  VISUAL 3: (Width: 55%)                                      |  VISUAL 4: (Width: 45%)             |
|  Top 10 High-Traffic Departure Stations (Clustered Bar)      |  Vehicle Fleet Share by User Type   |
|  X: Total Rides | Y: Station Name | Legend: User Type       |  Stacked Bar: Classic / E-Bike      |
+--------------------------------------------------------------+-------------------------------------+
```

### Visual Specifications
1. **Card 1 (Total Rides):**
   - Type: *Card (New)*
   - Value: `[Total Rides]`
   - Subtitle: `[YoY Ride Growth %]`
2. **Card 2 (Member Share):**
   - Type: *Card (New)*
   - Value: `[Member Ride Share %]`
   - Detail: `[Member Rides]` count
3. **Card 3 (Casual Share):**
   - Type: *Card (New)*
   - Value: `[Casual Ride Share %]`
   - Detail: `[Casual Rides]` count
4. **Card 4 (Avg Duration):**
   - Type: *Card (New)*
   - Value: `[Avg Ride Duration (Min)]`
   - Comparison: `Member: 12.8m vs Casual: 28.5m`
5. **Card 5 (Prime Conversion Pool):**
   - Type: *Card (New)*
   - Value: `[Prime Casual Conversion Pool]`
   - Detail: `Weekday Rush Hour Casuals`
6. **Visual 1 (Daily Trend with 7-Day MA):**
   - Type: *Line Chart*
   - X-Axis: `Dim_Date[Date]`
   - Y-Axis: `[Total Rides]`, `[7-Day Moving Avg Rides]`
   - Formatting: Observed line = Light Blue (`#93C5FD`), Moving average line = Coral Red (`#EF4444`) with 2.5px width.
7. **Visual 2 (Rider Split Donut):**
   - Type: *Donut Chart*
   - Legend: `Dim_UserType[User_Type_Name]`
   - Values: `[Total Rides]`
   - Formatting: Member = `#1D4ED8` (Blue), Casual = `#F97316` (Orange).
8. **Visual 3 (Top 10 Stations):**
   - Type: *Clustered Bar Chart (Horizontal)*
   - Y-Axis: `Dim_Station[Station_Name]` (Filtered by Top 10 by `[Total Rides]`)
   - X-Axis: `[Total Rides]`
   - Legend: `Dim_UserType[User_Type_Name]`
9. **Visual 4 (Bike Fleet Share):**
   - Type: *Clustered Column Chart*
   - X-Axis: `Dim_BikeType[Bike_Type_Name]`
   - Y-Axis: `[Total Rides]`
   - Legend: `Dim_UserType[User_Type_Name]`

---

## 👥 Page 2: Rider Personas & Behavioral Segmentation

**Page Purpose:** Demonstrates how annual members and casual riders use the bike-share network differently in time, duration, and purpose.

### Visual Layout & Configuration
1. **Callout Banner:** Highlights the core finding:
   > *"Members are utility-driven daily commuters (8 AM & 5 PM peaks, 12.8 min average). Casual riders are leisure-driven tourists and cruisers (afternoon peak, weekend surge, 28.5 min average)."*
2. **Visual 1: 24-Hour Departure Profile:**
   - Type: *Line Chart*
   - X-Axis: `Dim_Time[Hour_24]` (0 to 23)
   - Y-Axis: `[Member Rides]`, `[Casual Rides]`
   - Visual Impact: Shows the steep double peak for Members versus the single smooth afternoon bell curve for Casual riders.
3. **Visual 2: Trip Duration Buckets:**
   - Type: *100% Stacked Column Chart*
   - X-Axis: `Dim_UserType[User_Type_Name]`
   - Y-Axis: `[Total Rides]`
   - Legend: `Dim_RideCategory[Category_Name]` (Short <15m, Medium 15-60m, Long >60m)
4. **Visual 3: Day-of-Week Ridership Pattern:**
   - Type: *Clustered Column Chart*
   - X-Axis: `Dim_Date[Day_Of_Week_Name]` (Sorted Mon through Sun)
   - Y-Axis: `[Member Rides]`, `[Casual Rides]`
   - Insight: Members drop on Saturday/Sunday; Casual riders surge by **+185%**.
5. **Visual 4: K-Means Behavioral Cluster Table:**
   - Type: *Table / Matrix Visual*
   - Rows: `Fact_Rides[Cluster_ID]`
   - Columns: Cluster Name, Avg Duration (min), Avg Speed (km/h), Dominant Persona, Conversion Strategy.

---

## 📅 Page 3: Temporal Trends & Seasonality Dynamics

**Page Purpose:** Uncovers weather, seasonal, and intraday cycles to guide bike rebalancing, fleet maintenance scheduling, and seasonal marketing.

### Visual Layout & Configuration
1. **Visual 1: Monthly Ridership Seasonality & Quarter Breakdown:**
   - Type: *Area Chart*
   - X-Axis: `Dim_Date[Month_Name]` (Sorted Jan to Dec)
   - Y-Axis: `[Member Rides]`, `[Casual Rides]`
   - Insight: Summer surge (June-August) reaches nearly 4x winter low.
2. **Visual 2: 24x7 Ridership Heatmap Matrix:**
   - Type: *Matrix Visual*
   - Rows: `Dim_Date[Day_Of_Week_Name]` (Mon to Sun)
   - Columns: `Dim_Time[Hour_24]` (0 to 23)
   - Values: `[Total Rides]`
   - Formatting: Conditional Formatting > Background Color > Gradient:
     - Lowest value: Light Grey/Blue (`#EFF6FF`)
     - Mid-range: Medium Cobalt (`#93C5FD`)
     - Highest value: Deep Navy (`#1E3A8A`)
3. **Visual 3: Key Influencers Visual:**
   - Analyze: `Fact_Rides[Ride_Duration_Minutes]` (When is duration > 30 min?)
   - Explain by: `Dim_UserType[User_Type_Name]`, `Dim_Date[Day_Type]`, `Dim_Time[Time_Bucket]`, `Dim_BikeType[Bike_Type_Name]`.
4. **Visual 4: Decomposition Tree:**
   - Analyze: `[Total Rides]`
   - Explain by: `Dim_UserType[User_Type_Name]` ➔ `Dim_Date[Day_Type]` ➔ `Dim_Time[Time_Bucket]` ➔ `Dim_BikeType[Bike_Type_Name]`.

---

## 🗺️ Page 4: Geospatial & Station Network Intelligence

**Page Purpose:** Maps station volume, commuter corridors, and rebalancing imbalances across Chicago.

### Visual Layout & Configuration
1. **Visual 1: Chicago Station Map (Bubble Map / Azure Map):**
   - Type: *Map Visual / Azure Map*
   - Latitude: `Dim_Station[Latitude]`
   - Longitude: `Dim_Station[Longitude]`
   - Size: `[Total Rides]`
   - Color / Category: Color by `[Casual Ride Share %]` (Orange = High Casual, Blue = High Member)
   - Tooltips: Station Name, Community Area, Total Departures, Total Arrivals, Net Flow.
2. **Visual 2: Station Net Inflow / Outflow Balance:**
   - Type: *Diverging Bar Chart (Horizontal)*
   - Y-Axis: `Dim_Station[Station_Name]`
   - X-Axis: `[Station Net Inflow / Outflow Balance]`
   - Formatting: Positive values (Surplus) = Emerald Green (`#10B981`), Negative values (Deficit) = Crimson Red (`#EF4444`).
3. **Visual 3: Top 10 Origin-Destination Corridors:**
   - Type: *Table Visual*
   - Fields: `Fact_Rides[Route_Key]`, Start Station Name, End Station Name, `[Total Rides]`, `[Avg Ride Duration (Min)]`, `[Avg Trip Distance (KM)]`, `[Round Trip %]`.

---

## 🎯 Page 5: Strategic Conversion & Revenue Simulator (What-If)

**Page Purpose:** Enables executive scenario modeling to forecast Annual Recurring Revenue (ARR) gained by converting casual riders into annual members.

### Visual Layout & Configuration
1. **What-If Slider 1 (Conversion Rate %):**
   - Parameter: `WhatIf_ConversionRate`
   - Range: `1.0%` to `20.0%` (Step `0.5%`)
   - Default: `7.0%`
2. **What-If Slider 2 (Annual Membership Pricing):**
   - Parameter: `WhatIf_MembershipFee`
   - Range: `$89` to `$159` (Step `$5`)
   - Default: `$119`
3. **Simulation Output KPI Cards:**
   - Card 1: `[Simulated Converted Members]`
   - Card 2: `[Projected New Annual Revenue ($)]`
   - Card 3: `[Est Casual Single Ride Revenue ($)]` (Cannibalization offset)
   - Card 4: `[Net Conversion Revenue Uplift ($)]`
4. **Visual 1: High-Yield Station Conversion Hotspots Table:**
   - Displays stations with high casual riders displaying commuter patterns (e.g., Streeter Dr & Grand Ave, DuSable Lake Shore & Monroe).
   - Columns: Station Name, Casual Commuter Rides, Conversion Potential Tier, Marketing Campaign Action.
5. **Visual 2: Four-Stage Rider Conversion Funnel:**
   - Type: *Funnel Visual*
   - Stage 1: All Casual Riders (`100%`)
   - Stage 2: Repeat Casual Riders with ≥3 trips (`58.5%`)
   - Stage 3: Weekday Commuter Pattern Casuals (`41.4%`)
   - Stage 4: Target Converted Members (`[Selected Conversion Rate %]`)
6. **Visual 3: 2D Pricing & Conversion Sensitivity Matrix (Matrix Visual):**
   - Rows: Conversion Rate (3%, 5%, 7%, 10%, 15%)
   - Columns: Annual Subscription Price ($89, $109, $119, $139, $159)
   - Values: `[Net Conversion Revenue Uplift ($)]`
   - Formatting: Conditional formatting background color gradient (Red/Amber for low uplift to Deep Emerald Green for high uplift).

---

## 🏛️ Page 6: Executive Boardroom Briefing & Strategic Storytelling

**Page Purpose:** Formatted specifically as an executive board-level slide delivering crisp narrative storytelling, core empirical discoveries, and a 4-point commercial action plan.

### Visual Layout & Configuration
1. **Header Kicker & Title:**
   - Text: *"EXECUTIVE STRATEGY BRIEFING: Cyclistic Bike-Share: Annual Growth & Membership Strategy"*
2. **Three Empirical Pillars (Card Containers):**
   - **Pillar 01 (The Dual Persona Reality):** Highlights 55.2% member volume, 12.8m commuter duration vs. 28.5m leisure duration.
   - **Pillar 02 (The Commuter Casual Opportunity):** Identifies 11,480 weekday rush-hour casual rides representing **$1.36M addressable ARR**.
   - **Pillar 03 (Geographic Concentration):** Quantifies that 54% of all volume flows through the top 10 stations, with clear leisure vs. transit rail clusters.
3. **Four-Point Commercial Action Roadmap:**
   - **Initiative 1 (Digital Marketing):** Automated Commute Conversion in-app notifications.
   - **Initiative 2 (Physical Activation):** Field Ambassador QR Kiosks at Navy Pier & Millennium Park.
   - **Initiative 3 (Fleet Logistics):** Predictive morning rebalancing vans dispatched from surplus lakefront docks to deficit rail terminals.
   - **Initiative 4 (Product Packaging):** Spring Season Launch Pass to lock in annual commitments before summer tourist spikes.

---

## 💡 Strategic Recommendations for Cyclistic Leadership

1. **Station-Based Field Conversion Kiosks:**
   - Deploy brand ambassadors and QR code discount stations at top casual stations (Streeter Dr / Navy Pier, Millennium Park, Oak St Beach) targeting riders during Friday afternoon and weekend hours.
2. **Commuter "Try Before You Buy" Digital Push:**
   - Trigger automated in-app notifications to casual riders who complete weekday trips between 7–9 AM and 4–7 PM: *"You've commuted 3 times this week! An Annual Membership would save you $42/month."*
3. **Dynamic Rebalancing Routing:**
   - Use the **Station Net Flow** measures to optimize morning truck dispatch from surplus stations (lakefront/residential) to deficit stations (rail terminals: Ogilvie & Union Station).
4. **Seasonal Spring Membership Pass Launch:**
   - Launch annual membership discount campaigns in mid-April right before the May–July ridership explosion to capture casual summer tourists early.
