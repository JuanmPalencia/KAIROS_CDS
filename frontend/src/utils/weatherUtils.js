// WMO weather code mapping → [condition, alert_level, eta_multiplier, description]
export const WMO_MAP = {
  0:["CLEAR","GREEN",1,"Despejado"],        1:["CLEAR","GREEN",1,"Mayormente despejado"],
  2:["CLOUD","GREEN",1,"Parcialmente nublado"], 3:["CLOUD","GREEN",1,"Nublado"],
  45:["FOG","YELLOW",1.3,"Niebla"],         48:["FOG","YELLOW",1.3,"Niebla engelante"],
  51:["DRIZZLE","GREEN",1.05,"Llovizna ligera"], 53:["DRIZZLE","YELLOW",1.1,"Llovizna moderada"],
  55:["DRIZZLE","YELLOW",1.15,"Llovizna intensa"],
  56:["DRIZZLE","YELLOW",1.2,"Llovizna engelante"], 57:["DRIZZLE","ORANGE",1.3,"Llovizna engelante intensa"],
  61:["RAIN","YELLOW",1.2,"Lluvia ligera"],  63:["RAIN","ORANGE",1.3,"Lluvia moderada"],
  65:["RAIN","RED",1.5,"Lluvia intensa"],
  66:["RAIN","ORANGE",1.3,"Lluvia engelante"], 67:["RAIN","RED",1.5,"Lluvia engelante intensa"],
  71:["SNOW","ORANGE",1.5,"Nevada ligera"],  73:["SNOW","RED",1.7,"Nevada moderada"],
  75:["SNOW","RED",2.0,"Nevada intensa"],    77:["SNOW","ORANGE",1.4,"Granizo fino"],
  80:["SHOWERS","YELLOW",1.2,"Chubascos ligeros"], 81:["SHOWERS","ORANGE",1.4,"Chubascos moderados"],
  82:["SHOWERS","RED",1.6,"Chubascos fuertes"],
  85:["SNOW","ORANGE",1.5,"Chubascos de nieve"], 86:["SNOW","RED",1.8,"Chubascos de nieve fuertes"],
  95:["STORM","RED",1.8,"Tormenta"], 96:["STORM","RED",2.0,"Tormenta con granizo"],
  99:["STORM","RED",2.2,"Tormenta severa con granizo"],
};

export const COND_ICON = {
  CLEAR:"☀️", CLOUD:"☁️", FOG:"🌫️", DRIZZLE:"🌦️",
  RAIN:"🌧️", SHOWERS:"🌦️", SNOW:"❄️", STORM:"⛈️", HEAT:"🔥",
};
