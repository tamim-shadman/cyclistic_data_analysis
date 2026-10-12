/**
 * Cyclistic Bike-Share Star-Schema Dataset Generator for Power BI
 * Generates production-grade, statistically authentic CSV data for Power BI Desktop.
 */

const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.join(__dirname, 'data');
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

console.log('🚴 Starting Cyclistic Power BI Dataset Generation...');

// ==========================================
// 1. STATIONS DEFINITIONS (Authentic Chicago)
// ==========================================
const STATIONS = [
  { id: 101, name: "Streeter Dr & Grand Ave", lat: 41.892278, lng: -87.612043, area: "Streeterville / Navy Pier", tier: "Tier 1 Lakefront Leisure", casualBias: 0.82 },
  { id: 102, name: "DuSable Lake Shore Dr & Monroe St", lat: 41.880958, lng: -87.616743, area: "Loop / Millennium Park", tier: "Tier 1 Lakefront Leisure", casualBias: 0.78 },
  { id: 103, name: "Michigan Ave & Oak St", lat: 41.900960, lng: -87.623777, area: "Gold Coast / Beach", tier: "Tier 1 Lakefront Leisure", casualBias: 0.72 },
  { id: 104, name: "Millennium Park", lat: 41.881032, lng: -87.624084, area: "Loop", tier: "Tier 1 Tourist Center", casualBias: 0.75 },
  { id: 105, name: "Theater on the Lake", lat: 41.926277, lng: -87.630831, area: "Lincoln Park Lakefront", tier: "Tier 1 Lakefront Leisure", casualBias: 0.76 },
  { id: 106, name: "Shedd Aquarium", lat: 41.867226, lng: -87.615355, area: "Museum Campus", tier: "Tier 1 Tourist Center", casualBias: 0.79 },
  { id: 201, name: "Clinton St & Washington Blvd", lat: 41.883380, lng: -87.641170, area: "West Loop / Ogilvie Station", tier: "Tier 1 Commuter Hub", casualBias: 0.14 },
  { id: 202, name: "Clinton St & Madison St", lat: 41.882242, lng: -87.641066, area: "West Loop / Union Station", tier: "Tier 1 Commuter Hub", casualBias: 0.16 },
  { id: 203, name: "Canal St & Adams St", lat: 41.879255, lng: -87.639904, area: "West Loop / Union Station", tier: "Tier 1 Commuter Hub", casualBias: 0.18 },
  { id: 204, name: "Kingsbury St & Kinzie St", lat: 41.889177, lng: -87.638506, area: "Fulton River District", tier: "Tier 1 Commuter Hub", casualBias: 0.22 },
  { id: 205, name: "Clark St & Elm St", lat: 41.902973, lng: -87.631280, area: "Near North Side", tier: "Tier 2 Mixed Commuter/Res", casualBias: 0.32 },
  { id: 206, name: "Wells St & Concord Ln", lat: 41.912133, lng: -87.634656, area: "Old Town", tier: "Tier 2 Residential Corridor", casualBias: 0.34 },
  { id: 207, name: "Dearborn St & Adams St", lat: 41.879356, lng: -87.629791, area: "Financial District / Loop", tier: "Tier 1 Commuter Hub", casualBias: 0.21 },
  { id: 208, name: "Franklin St & Monroe St", lat: 41.880317, lng: -87.635185, area: "Loop Business Core", tier: "Tier 1 Commuter Hub", casualBias: 0.19 },
  { id: 209, name: "Broadway & Barry Ave", lat: 41.937725, lng: -87.644095, area: "Lakeview", tier: "Tier 2 Mixed Urban", casualBias: 0.38 },
  { id: 210, name: "Wilton Ave & Belmont Ave", lat: 41.940180, lng: -87.653030, area: "Lakeview / CTA Hub", tier: "Tier 2 Transit Transfer", casualBias: 0.28 },
  { id: 301, name: "State St & 33rd St", lat: 41.834734, lng: -87.625827, area: "Bronzeville / IIT", tier: "Tier 3 University / South", casualBias: 0.35 },
  { id: 302, name: "University Ave & 57th St", lat: 41.791478, lng: -87.599861, area: "Hyde Park / UChicago", tier: "Tier 3 University Campus", casualBias: 0.31 },
  { id: 303, name: "Halsted St & 18th St", lat: 41.857506, lng: -87.646277, area: "Pilsen Arts District", tier: "Tier 3 Neighborhood Hub", casualBias: 0.44 },
  { id: 304, name: "Damen Ave & Cortland St", lat: 41.916045, lng: -87.677412, area: "Bucktown / 606 Trail", tier: "Tier 2 Neighborhood Trail", casualBias: 0.48 }
];

// Helper: Haversine distance in KM
function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371; // km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return parseFloat((R * c).toFixed(2));
}

// ==========================================
// 2. DIMENSION TABLES WRITING
// ==========================================

// Dim_UserType.csv
const userTypeData = `user_type_key,user_type_name,target_persona,strategic_goal
1,Member,Daily Commuter / Routine Rider,Retention & Annual Renewal
2,Casual,Leisure Rider / Tourist / Weekend Cruiser,Annual Membership Conversion
`;
fs.writeFileSync(path.join(OUTPUT_DIR, 'Dim_UserType.csv'), userTypeData);

// Dim_BikeType.csv
const bikeTypeData = `bike_type_key,bike_type_name,speed_rating,fleet_role
1,Classic Bike,Standard (12-15 km/h),Core Commuter Fleet
2,Electric Bike,Fast (18-22 km/h),High Demand / Longer Trips
3,Docked Bike,Standard (12-15 km/h),Legacy Station Fleet
`;
fs.writeFileSync(path.join(OUTPUT_DIR, 'Dim_BikeType.csv'), bikeTypeData);

// Dim_RideCategory.csv
const rideCategoryData = `category_key,category_name,min_minutes,max_minutes,persona_fit
1,Short Trip (<15 min),1,15,Last-Mile Transit / Quick Errand
2,Medium Trip (15-60 min),15,60,Primary Commute / Recreational Route
3,Long / Day Trip (>60 min),60,1440,Lakefront Touring / Heavy Leisure
`;
fs.writeFileSync(path.join(OUTPUT_DIR, 'Dim_RideCategory.csv'), rideCategoryData);

// Dim_Station.csv
let stationCsv = "station_id,station_name,latitude,longitude,community_area,station_tier,casual_bias_ratio\n";
for (const s of STATIONS) {
  stationCsv += `${s.id},"${s.name}",${s.lat},${s.lng},"${s.area}","${s.tier}",${s.casualBias}\n`;
}
fs.writeFileSync(path.join(OUTPUT_DIR, 'Dim_Station.csv'), stationCsv);

// Dim_Time.csv
let timeCsv = "time_key,hour_24,hour_12,am_pm,hour_label,time_bucket,is_peak_rush_hour\n";
for (let h = 0; h < 24; h++) {
  const timeKey = `${String(h).padStart(2, '0')}:00`;
  const h12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
  const ampm = h < 12 ? "AM" : "PM";
  const label = `${h12} ${ampm}`;
  let bucket = "Night (20:00 - 23:00)";
  if (h >= 0 && h < 6) bucket = "Early Morning (00:00 - 06:00)";
  else if (h >= 7 && h <= 9) bucket = "Morning Rush (07:00 - 09:00)";
  else if (h >= 10 && h <= 15) bucket = "Midday (10:00 - 15:00)";
  else if (h >= 16 && h <= 19) bucket = "Evening Rush (16:00 - 19:00)";
  
  const isPeak = (h >= 7 && h <= 9) || (h >= 16 && h <= 19) ? 1 : 0;
  timeCsv += `"${timeKey}",${h},${h12},"${ampm}","${label}","${bucket}",${isPeak}\n`;
}
fs.writeFileSync(path.join(OUTPUT_DIR, 'Dim_Time.csv'), timeCsv);

// Dim_Date.csv (Full calendar year 2025)
let dateCsv = "date_key,date,year,quarter,month_number,month_name,month_short,month_year,week_number,day_of_week_number,day_of_week_name,day_short,is_weekend_flag,day_type\n";
const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

const startDate = new Date(2025, 0, 1);
const endDate = new Date(2025, 11, 31);
let curDate = new Date(startDate);

while (curDate <= endDate) {
  const y = curDate.getFullYear();
  const m = curDate.getMonth(); // 0-11
  const d = curDate.getDate();
  const dow = curDate.getDay(); // 0 = Sun, 1 = Mon ...
  const dateKey = y * 10000 + (m + 1) * 100 + d;
  const dateStr = `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
  const quarter = `Q${Math.floor(m / 3) + 1}`;
  const mName = months[m];
  const mShort = mName.substring(0, 3);
  const mYear = `${mShort} ${y}`;
  
  // Week number estimation
  const firstDayOfYear = new Date(y, 0, 1);
  const pastDaysOfYear = (curDate - firstDayOfYear) / 86400000;
  const weekNum = Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);

  // Day of week number where Monday = 1, Sunday = 7
  const dowNum = dow === 0 ? 7 : dow;
  const dName = days[dow];
  const dShort = dName.substring(0, 3);
  const isWeekend = (dow === 0 || dow === 6) ? 1 : 0;
  const dayType = isWeekend === 1 ? "Weekend" : "Weekday";

  dateCsv += `${dateKey},${dateStr},${y},"${quarter}",${m + 1},"${mName}","${mShort}","${mYear}",${weekNum},${dowNum},"${dName}","${dShort}",${isWeekend},"${dayType}"\n`;
  curDate.setDate(curDate.getDate() + 1);
}
fs.writeFileSync(path.join(OUTPUT_DIR, 'Dim_Date.csv'), dateCsv);

console.log('✅ Dimension tables created successfully.');

// ==========================================
// 3. FACT_RIDES GENERATION (60,000 High-Fidelity Records)
// ==========================================
const TOTAL_RECORDS = 60000;
const factPath = path.join(OUTPUT_DIR, 'Fact_Rides.csv');
const writeStream = fs.createWriteStream(factPath);

writeStream.write("ride_id,date_key,time_key,user_type_key,bike_type_key,ride_category_key,start_station_id,end_station_id,route_key,ride_duration_minutes,distance_km,speed_kmh,is_round_trip,cluster_id\n");

// Seasonal factors (1 = normal, winter lower, summer higher)
const seasonalMultiplier = [0.35, 0.40, 0.65, 0.90, 1.30, 1.65, 1.85, 1.75, 1.45, 1.10, 0.60, 0.45];

let idCounter = 1000000;
let generated = 0;

// Random normal approximation
function randomNorm(mean, stdev) {
  let u = 1 - Math.random();
  let v = Math.random();
  let z = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
  return mean + z * stdev;
}

// Generate rides across all 365 days of 2025
let simDate = new Date(2025, 0, 1);
const allDates = [];
while (simDate <= endDate) {
  allDates.push(new Date(simDate));
  simDate.setDate(simDate.getDate() + 1);
}

for (const dateObj of allDates) {
  const y = dateObj.getFullYear();
  const m = dateObj.getMonth();
  const d = dateObj.getDate();
  const dow = dateObj.getDay();
  const isWeekend = (dow === 0 || dow === 6);
  const dateKey = y * 10000 + (m + 1) * 100 + d;

  // Rides per day based on season & day type
  const baseDayRides = isWeekend ? 190 : 155;
  const dailyTarget = Math.round(baseDayRides * seasonalMultiplier[m] * (0.85 + Math.random() * 0.3));

  for (let r = 0; r < dailyTarget; r++) {
    idCounter++;
    generated++;

    // User Type determination
    // Weekday: ~68% Members, ~32% Casuals
    // Weekend: ~38% Members, ~62% Casuals
    let isMember = isWeekend ? (Math.random() < 0.38) : (Math.random() < 0.68);
    const userTypeKey = isMember ? 1 : 2;

    // Hourly distribution
    let hour = 12;
    if (isMember) {
      if (!isWeekend) {
        // Commuter peaks at 8 AM and 5 PM
        const rVal = Math.random();
        if (rVal < 0.42) hour = Math.floor(randomNorm(8, 0.9)); // morning rush
        else if (rVal < 0.85) hour = Math.floor(randomNorm(17, 1.1)); // evening rush
        else hour = Math.floor(randomNorm(13, 3.2));
      } else {
        hour = Math.floor(randomNorm(14, 3.0));
      }
    } else {
      // Casual riders peak between 13:00 and 17:00
      hour = Math.floor(randomNorm(15, 2.8));
    }
    hour = Math.max(0, Math.min(23, hour));
    const timeKey = `${String(hour).padStart(2, '0')}:00`;

    // Bike type selection: Electric 46%, Classic 47%, Docked 7% (Docked is casual only)
    let bikeTypeKey = 1;
    const bikeRand = Math.random();
    if (!isMember && bikeRand < 0.12) {
      bikeTypeKey = 3; // Docked
    } else if (bikeRand < 0.50) {
      bikeTypeKey = 2; // Electric
    } else {
      bikeTypeKey = 1; // Classic
    }

    // Station selection
    let startStation;
    if (isMember) {
      // Commuter preference (Clinton St, Loop, West Loop)
      const commuterStations = STATIONS.filter(s => s.casualBias < 0.35);
      startStation = commuterStations[Math.floor(Math.random() * commuterStations.length)];
    } else {
      // Leisure preference (Streeter Dr, Millennium, Beach)
      const leisureStations = STATIONS.filter(s => s.casualBias >= 0.50);
      startStation = leisureStations[Math.floor(Math.random() * leisureStations.length)];
    }

    // End station selection
    let endStation;
    const isRoundTrip = (!isMember && Math.random() < 0.18) ? 1 : 0;
    if (isRoundTrip) {
      endStation = startStation;
    } else {
      // Destination station
      let candidates = STATIONS.filter(s => s.id !== startStation.id);
      endStation = candidates[Math.floor(Math.random() * candidates.length)];
    }

    // Trip duration calculation
    let duration;
    if (isMember) {
      duration = Math.max(2, Math.round(randomNorm(12.8, 5.5)));
    } else {
      duration = Math.max(4, Math.round(randomNorm(28.5, 14.2)));
    }
    // Cap duration to realistic Cyclistic bounds
    duration = Math.min(360, Math.max(1, duration));

    // Distance calculation
    let distance = haversine(startStation.lat, startStation.lng, endStation.lat, endStation.lng);
    if (isRoundTrip || distance === 0) {
      // Round trip approximate loop distance based on duration
      distance = parseFloat(((duration * 0.22)).toFixed(2));
    }
    distance = Math.max(0.4, distance);

    // Speed km/h
    const speed = parseFloat(((distance / (duration / 60))).toFixed(1));

    // Ride Category Key
    let catKey = 1;
    if (duration <= 15) catKey = 1;
    else if (duration <= 60) catKey = 2;
    else catKey = 3;

    // Cluster ID (K-Means simulation: 1=Fast Commute, 2=Leisure Cruiser, 3=Long Distance, 4=Quick Errand)
    let clusterId = 1;
    if (isMember && duration < 20 && speed >= 13) clusterId = 1;
    else if (!isMember && duration >= 25) clusterId = 2;
    else if (distance >= 5.0) clusterId = 3;
    else clusterId = 4;

    const routeKey = `"${startStation.id}-${endStation.id}"`;
    const rideId = `"CR-${idCounter}"`;

    writeStream.write(`${rideId},${dateKey},"${timeKey}",${userTypeKey},${bikeTypeKey},${catKey},${startStation.id},${endStation.id},${routeKey},${duration},${distance},${speed},${isRoundTrip},${clusterId}\n`);
  }
}

writeStream.end(() => {
  console.log(`✅ Generated ${generated.toLocaleString()} Fact_Rides records!`);
  console.log(`📁 All Star-Schema files ready in: ${OUTPUT_DIR}`);
});
