export const GREETING_CONFIG = {
  timeZone: "Asia/Kolkata",
  morningStartHour: 4,
  eveningStartHour: 12,
  nightStartHour: 21,
};

export function getCurrentKolkataDate(date = new Date()) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: GREETING_CONFIG.timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).formatToParts(date);
}

export function getCurrentKolkataHour(date = new Date()) {
  const parts = getCurrentKolkataDate(date);
  const lookup = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return Number(lookup.hour || 0);
}

export function getGreetingMeta(date = new Date()) {
  const hour = getCurrentKolkataHour(date);

  if (hour >= GREETING_CONFIG.morningStartHour && hour < GREETING_CONFIG.eveningStartHour) {
    return { label: "morning", text: "Good morning" };
  }

  if (hour >= GREETING_CONFIG.eveningStartHour && hour < GREETING_CONFIG.nightStartHour) {
    return { label: "evening", text: "Good evening" };
  }

  return { label: "night", text: "Good night" };
}

export function getGreetingText(userName, date = new Date()) {
  const cleanedName = (userName || "User").trim();
  const { text } = getGreetingMeta(date);
  return `${text}, ${cleanedName}. How can I help you?`;
}
