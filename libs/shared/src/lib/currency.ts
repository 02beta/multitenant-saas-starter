/**
 * Currency utility functions for handling monetary values.
 * All functions are typesafe and functions that work with cents
 * assume integer values representing the smallest currency unit.
 */

/**
 * Get the absolute value of currency amount.
 * @param cents - The amount in cents
 * @returns The absolute value of the amount in cents
 */
export function absoluteCurrency(cents: number): number {
  return Math.abs(cents);
}

/**
 * Add two currency amounts in cents.
 * @param cents1 - The first amount in cents
 * @param cents2 - The second amount in cents
 * @returns The sum of both amounts in cents
 */
export function addCurrency(cents1: number, cents2: number): number {
  return cents1 + cents2;
}

/**
 * Apply discount to currency amount.
 * @param cents - The original amount in cents
 * @param discountPercentage - The discount percentage to apply (e.g., 10 for 10% off)
 * @returns The discounted amount in cents
 */
export function applyDiscount(
  cents: number,
  discountPercentage: number
): number {
  return cents - calculatePercentage(cents, discountPercentage);
}

/**
 * Apply tax to currency amount.
 * @param cents - The base amount in cents
 * @param taxPercentage - The tax percentage to apply (e.g., 8.5 for 8.5% tax)
 * @returns The amount with tax applied in cents
 */
export function applyTax(cents: number, taxPercentage: number): number {
  return cents + calculatePercentage(cents, taxPercentage);
}

/**
 * Calculate percentage of currency amount.
 * @param cents - The base amount in cents
 * @param percentage - The percentage to calculate (e.g., 15 for 15%)
 * @returns The calculated percentage amount in cents
 */
export function calculatePercentage(cents: number, percentage: number): number {
  return Math.round(cents * (percentage / 100));
}

/**
 * Convert cents to dollars for display.
 * @param cents - The cent amount to convert
 * @returns The equivalent amount in dollars
 */
export function centsToDollars(cents: number): number {
  return cents / 100;
}

/**
 * Compare two currency amounts.
 * @param cents1 - The first amount in cents
 * @param cents2 - The second amount in cents
 * @returns Negative if cents1 < cents2, positive if cents1 > cents2, zero if equal
 */
export function compareCurrency(cents1: number, cents2: number): number {
  return cents1 - cents2;
}

/**
 * Convert between different currency units using an exchange rate.
 * @param cents - The amount in cents to convert
 * @param exchangeRate - The exchange rate to apply
 * @returns The converted amount in cents, rounded to the nearest cent
 */
export function convertCurrency(cents: number, exchangeRate: number): number {
  return Math.round(cents * exchangeRate);
}

/**
 * Divide currency amount by a divisor.
 * @param cents - The amount in cents to divide
 * @param divisor - The division factor
 * @returns The result rounded to the nearest cent
 */
export function divideCurrency(cents: number, divisor: number): number {
  return Math.round(cents / divisor);
}

/**
 * Convert dollars to cents for storage.
 * @param dollars - The dollar amount to convert
 * @returns The equivalent amount in cents
 */
export function dollarsToCents(dollars: number): number {
  return Math.round(dollars * 100);
}

/**
 * Format dollars as currency string.
 * @param dollars - The amount in dollars to format
 * @param currency - The currency code (default: "USD")
 * @param locale - The locale for formatting (default: "en-US")
 * @returns Formatted currency string
 */
export function formatDollars(
  dollars: number,
  currency = "USD",
  locale = "en-US"
): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: currency,
  }).format(dollars);
}

/**
 * Format cents as currency string.
 * @param cents - The amount in cents to format
 * @param currency - The currency code (default: "USD")
 * @param locale - The locale for formatting (default: "en-US")
 * @returns Formatted currency string
 */
export function formatPrice(
  cents: number,
  currency = "USD",
  locale = "en-US"
): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: currency,
  }).format(centsToDollars(cents));
}

/**
 * Get currency symbol for a given currency code.
 * @param currency - The currency code (default: "USD")
 * @param locale - The locale for formatting (default: "en-US")
 * @returns The currency symbol (e.g., "$" for USD)
 */
export function getCurrencySymbol(currency = "USD", locale = "en-US"): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })
    .format(0)
    .replace(/\d/g, "")
    .trim();
}

/**
 * Check if currency amount is valid (non-negative and finite).
 * @param cents - The amount in cents to validate
 * @returns True if the amount is valid, false otherwise
 */
export function isValidCurrency(cents: number): boolean {
  return typeof cents === "number" && cents >= 0 && Number.isFinite(cents);
}

/**
 * Multiply currency amount by a factor.
 * @param cents - The amount in cents to multiply
 * @param factor - The multiplication factor
 * @returns The result rounded to the nearest cent
 */
export function multiplyCurrency(cents: number, factor: number): number {
  return Math.round(cents * factor);
}

/**
 * Parse currency string to cents.
 * @param currencyString - The currency string to parse (e.g., "$12.34")
 * @returns The equivalent amount in cents, or 0 if parsing fails
 */
export function parseCurrencyToCents(currencyString: string): number {
  const cleaned = currencyString.replace(/[^0-9.-]/g, "");
  const dollars = parseFloat(cleaned);
  return isNaN(dollars) ? 0 : dollarsToCents(dollars);
}

/**
 * Parse currency string to dollars.
 * @param currencyString - The currency string to parse (e.g., "$12.34")
 * @returns The equivalent amount in dollars, or 0 if parsing fails
 */
export function parseCurrencyToDollars(currencyString: string): number {
  const cleaned = currencyString.replace(/[^0-9.-]/g, "");
  const dollars = parseFloat(cleaned);
  return isNaN(dollars) ? 0 : dollars;
}

/**
 * Round currency to nearest cent.
 * @param dollars - The dollar amount to round
 * @returns The amount rounded to the nearest cent
 */
export function roundToCents(dollars: number): number {
  return Math.round(dollars * 100) / 100;
}

/**
 * Subtract two currency amounts in cents.
 * @param cents1 - The amount to subtract from (in cents)
 * @param cents2 - The amount to subtract (in cents)
 * @returns The difference in cents
 */
export function subtractCurrency(cents1: number, cents2: number): number {
  return cents1 - cents2;
}
