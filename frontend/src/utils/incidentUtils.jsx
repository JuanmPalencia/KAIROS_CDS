import { Heart, Wind, Brain, Zap, Flame, Skull, HeartPulse, Baby, Smile, Shield, Sparkles, Thermometer, Pill, Waves, PersonStanding, AlertTriangle } from 'lucide-react';

export function getIncidentTypeLabel(type) {
  const labels = {
    CARDIO:       { icon: Heart,          text: "Cardíaco" },
    RESPIRATORY:  { icon: Wind,           text: "Respiratorio" },
    NEUROLOGICAL: { icon: Brain,          text: "Neurológico" },
    TRAUMA:       { icon: Zap,            text: "Trauma" },
    BURN:         { icon: Flame,          text: "Quemadura" },
    POISONING:    { icon: Skull,          text: "Intoxicación" },
    OBSTETRIC:    { icon: HeartPulse,     text: "Obstétrico" },
    PEDIATRIC:    { icon: Baby,           text: "Pediátrico" },
    PSYCHIATRIC:  { icon: Smile,          text: "Psiquiátrico" },
    VIOLENCE:     { icon: Shield,         text: "Violencia" },
    ALLERGIC:     { icon: Sparkles,       text: "Alérgico" },
    METABOLIC:    { icon: Thermometer,    text: "Metabólico" },
    INTOXICATION: { icon: Pill,           text: "Intoxicación (drogas)" },
    DROWNING:     { icon: Waves,          text: "Ahogamiento" },
    FALL:         { icon: PersonStanding, text: "Caída" },
    GENERAL:      { icon: AlertTriangle,  text: "General" },
  };
  const entry = labels[type];
  if (!entry) return type;
  const Icon = entry.icon;
  return <><Icon size={14} /> {entry.text}</>;
}
