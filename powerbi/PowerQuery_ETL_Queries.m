// ==============================================================================
// CYCLISTIC BIKE-SHARE ANALYTICS — POWER QUERY (M) ETL CODE LIBRARY
// Paste each query into Power BI Desktop via: Home -> Advanced Editor
// ==============================================================================

// ------------------------------------------------------------------------------
// QUERY 1: Dim_Date (Dynamic Calendar Table)
// ------------------------------------------------------------------------------
let
    // Define date boundaries (automatically adjusted or hardcoded)
    StartDate = #date(2025, 1, 1),
    EndDate = #date(2025, 12, 31),
    DayCount = Duration.Days(Duration.From(EndDate - StartDate)) + 1,
    Source = List.Dates(StartDate, DayCount, #duration(1, 0, 0, 0)),
    #"Converted to Table" = Table.FromList(Source, Splitter.SplitByNothing(), {"Date"}, null, ExtraValues.Error),
    #"Changed Type" = Table.TransformColumnTypes(#"Converted to Table",{{"Date", type date}}),
    #"Added DateKey" = Table.AddColumn(#"Changed Type", "Date_Key", each Date.Year([Date]) * 10000 + Date.Month([Date]) * 100 + Date.Day([Date]), Int64.Type),
    #"Added Year" = Table.AddColumn(#"Added DateKey", "Year", each Date.Year([Date]), Int64.Type),
    #"Added Quarter" = Table.AddColumn(#"Added Year", "Quarter", each "Q" & Text.From(Date.QuarterOfYear([Date])), type text),
    #"Added Month Number" = Table.AddColumn(#"Added Quarter", "Month_Number", each Date.Month([Date]), Int64.Type),
    #"Added Month Name" = Table.AddColumn(#"Added Month Number", "Month_Name", each Date.MonthName([Date]), type text),
    #"Added Month Short" = Table.AddColumn(#"Added Month Name", "Month_Short", each Text.Start([Month_Name], 3), type text),
    #"Added Month-Year" = Table.AddColumn(#"Added Month Short", "Month_Year", each Text.Start([Month_Name], 3) & " " & Text.From([Year]), type text),
    #"Added Week of Year" = Table.AddColumn(#"Added Month-Year", "Week_Number", each Date.WeekOfYear([Date]), Int64.Type),
    #"Added Day of Week" = Table.AddColumn(#"Added Week of Year", "Day_Of_Week_Number", each Date.DayOfWeek([Date], Day.Monday) + 1, Int64.Type),
    #"Added Day Name" = Table.AddColumn(#"Added Day of Week", "Day_Of_Week_Name", each Date.DayOfWeekName([Date]), type text),
    #"Added Day Short" = Table.AddColumn(#"Added Day Name", "Day_Short", each Text.Start([Day_Of_Week_Name], 3), type text),
    #"Added Is Weekend" = Table.AddColumn(#"Added Day Short", "Is_Weekend_Flag", each if [Day_Of_Week_Number] >= 6 then 1 else 0, Int64.Type),
    #"Added Day Type" = Table.AddColumn(#"Added Is Weekend", "Day_Type", each if [Is_Weekend_Flag] = 1 then "Weekend" else "Weekday", type text)
in
    #"Added Day Type"


// ------------------------------------------------------------------------------
// QUERY 2: Dim_Time (24-Hour Time Dimension)
// ------------------------------------------------------------------------------
let
    Source = List.Numbers(0, 24, 1),
    #"Converted to Table" = Table.FromList(Source, Splitter.SplitByNothing(), {"Hour_24"}, null, ExtraValues.Error),
    #"Changed Type" = Table.TransformColumnTypes(#"Converted to Table",{{"Hour_24", Int64.Type}}),
    #"Added Time Key" = Table.AddColumn(#"Changed Type", "Time_Key", each Text.PadStart(Text.From([Hour_24]), 2, "0") & ":00", type text),
    #"Added Hour 12" = Table.AddColumn(#"Added Time Key", "Hour_12", each if [Hour_24] = 0 then 12 else if [Hour_24] > 12 then [Hour_24] - 12 else [Hour_24], Int64.Type),
    #"Added AM PM" = Table.AddColumn(#"Added Hour 12", "AM_PM", each if [Hour_24] < 12 then "AM" else "PM", type text),
    #"Added Hour Label" = Table.AddColumn(#"Added AM PM", "Hour_Label", each Text.From([Hour_12]) & " " & [AM_PM], type text),
    #"Added Time Bucket" = Table.AddColumn(#"Added Hour Label", "Time_Bucket", each 
        if [Hour_24] >= 0 and [Hour_24] < 6 then "Early Morning (00:00 - 06:00)"
        else if [Hour_24] >= 7 and [Hour_24] <= 9 then "Morning Rush (07:00 - 09:00)"
        else if [Hour_24] >= 10 and [Hour_24] <= 15 then "Midday (10:00 - 15:00)"
        else if [Hour_24] >= 16 and [Hour_24] <= 19 then "Evening Rush (16:00 - 19:00)"
        else "Night (20:00 - 23:00)", type text),
    #"Added Peak Commute Flag" = Table.AddColumn(#"Added Time Bucket", "Is_Peak_Rush_Hour", each 
        if ([Hour_24] >= 7 and [Hour_24] <= 9) or ([Hour_24] >= 16 and [Hour_24] <= 19) then 1 else 0, Int64.Type)
in
    #"Added Peak Commute Flag"


// ------------------------------------------------------------------------------
// QUERY 3: Dim_UserType (User Segmentation Dimension)
// ------------------------------------------------------------------------------
let
    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("i45WMlTSUXIEYoPQkGCl2FgA", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [User_Type_Key = _t, User_Type_Name = _t, Target_Persona = _t, Strategic_Goal = _t]),
    // Alternatively manually entered:
    TableData = Table.FromRecords({
        [User_Type_Key = 1, User_Type_Name = "Member", Target_Persona = "Daily Commuter / Routine Rider", Strategic_Goal = "Retention, Fleet Loyalty & Upsell"],
        [User_Type_Key = 2, User_Type_Name = "Casual", Target_Persona = "Leisure Rider / Tourist / Weekend Cruiser", Strategic_Goal = "Annual Membership Conversion"]
    }),
    #"Changed Type" = Table.TransformColumnTypes(TableData,{{"User_Type_Key", Int64.Type}, {"User_Type_Name", type text}, {"Target_Persona", type text}, {"Strategic_Goal", type text}})
in
    #"Changed Type"


// ------------------------------------------------------------------------------
// QUERY 4: Dim_BikeType (Vehicle Dimension)
// ------------------------------------------------------------------------------
let
    TableData = Table.FromRecords({
        [Bike_Type_Key = 1, Bike_Type_Name = "Classic Bike", Speed_Rating = "Standard (12-15 km/h)", Fleet_Role = "Core Commuter Workhorse"],
        [Bike_Type_Key = 2, Bike_Type_Name = "Electric Bike", Speed_Rating = "Fast (18-22 km/h)", Fleet_Role = "High Demand / Longer Commutes"],
        [Bike_Type_Key = 3, Bike_Type_Name = "Docked Bike", Speed_Rating = "Standard (12-15 km/h)", Fleet_Role = "Legacy Station Fleet"]
    }),
    #"Changed Type" = Table.TransformColumnTypes(TableData,{{"Bike_Type_Key", Int64.Type}, {"Bike_Type_Name", type text}, {"Speed_Rating", type text}, {"Fleet_Role", type text}})
in
    #"Changed Type"


// ------------------------------------------------------------------------------
// QUERY 5: Dim_RideCategory (Trip Duration Buckets)
// ------------------------------------------------------------------------------
let
    TableData = Table.FromRecords({
        [Category_Key = 1, Category_Name = "Short Trip (<15 min)", Min_Min = 1, Max_Min = 15, Persona_Fit = "Last-Mile Transit / Quick Errand"],
        [Category_Key = 2, Category_Name = "Medium Trip (15-60 min)", Min_Min = 15, Max_Min = 60, Persona_Fit = "Primary Commute / Recreational Route"],
        [Category_Key = 3, Category_Name = "Long / Day Trip (>60 min)", Min_Min = 60, Max_Min = 1440, Persona_Fit = "Lakefront Touring / Heavy Leisure"]
    }),
    #"Changed Type" = Table.TransformColumnTypes(TableData,{{"Category_Key", Int64.Type}, {"Category_Name", type text}, {"Min_Min", Int64.Type}, {"Max_Min", Int64.Type}, {"Persona_Fit", type text}})
in
    #"Changed Type"


// ------------------------------------------------------------------------------
// QUERY 6: Fact_Rides (Extract, Clean, Transform Pipeline)
// Loads raw CSV/Parquet file, applies identical Python cleaning rules:
// - Duration between 1 and 1440 minutes
// - Extracts DateKey and TimeKey
// - Haversine distance in KM
// - Assigns keys to link with dimensions
// ------------------------------------------------------------------------------
// (Configure the Source path to your data folder or Fact_Rides.csv)
/*
let
    Source = Csv.Document(File.Contents("C:\YourPath\Fact_Rides.csv"), [Delimiter=",", Columns=16, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Types" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"ride_id", type text},
        {"date_key", Int64.Type},
        {"time_key", type text},
        {"user_type_key", Int64.Type},
        {"bike_type_key", Int64.Type},
        {"ride_category_key", Int64.Type},
        {"start_station_id", Int64.Type},
        {"end_station_id", Int64.Type},
        {"ride_duration_minutes", type number},
        {"distance_km", type number},
        {"speed_kmh", type number},
        {"is_round_trip", Int64.Type},
        {"cluster_id", Int64.Type}
    })
in
    #"Changed Types"
*/
