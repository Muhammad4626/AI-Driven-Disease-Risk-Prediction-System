import apiClient from "../api/apiClients";

export type PredictQuery = {
  // Backend expects this as `district_name` query param.//
  district_name: string;
  /** Backend expects integer `year` (2000–2100). */
  year: number;
  /** Backend expects integer `week_number` (1–53). */
  week_number: number;
};

export type PredictionValues = {
  malaria_risk_next_week: number;
  ad_risk_next_week: number;
  typhoid_risk_next_week: number;
  avg_temperature: number;
  avg_rainfall: number;
  avg_humidity: number;
  flood_inundation: number;
  stagnant_water: number;
  mean_ndvi: number;
};

export type ExplanationImages = {
  /** Full data-URL, e.g. `data:image/png;base64,...` */
  waterfall_plot: string;
  /** Full data-URL, e.g. `data:image/png;base64,...` */
  bar_plot: string;
};

export type DiseaseExplanations = {
  malaria: ExplanationImages;
  ad: ExplanationImages;
  typhoid: ExplanationImages;
};

export type PredictionValuesWithExplanations = PredictionValues & {
  /**
   * SHAP plots for each disease.
   * Optional for backward-compatibility with older backend builds.
   */
  explanations?: DiseaseExplanations;
};

export type PredictResponse = {
  district_name: string;
  year: number;
  week_number: number;
  predictions: PredictionValuesWithExplanations;
};

function buildPredictPath(q: PredictQuery): string {
  const districtName = q.district_name?.trim();
  if (!districtName) {
    throw new Error("district_name is required");
  }
  if (!Number.isInteger(q.year)) {
    throw new Error("year must be an integer");
  }
  if (q.year < 2000 || q.year > 2100) {
    throw new Error("year must be between 2000 and 2100");
  }
  if (!Number.isInteger(q.week_number)) {
    throw new Error("week_number must be an integer");
  }
  if (q.week_number < 1 || q.week_number > 53) {
    throw new Error("week_number must be between 1 and 53");
  }

  const params = new URLSearchParams({
    district_name: districtName,
    year: String(q.year),
    week_number: String(q.week_number),
  });

  return `/predict?${params.toString()}`;
}

function extractBackendErrorMessage(err: unknown): string {
  if (err instanceof Error) {
    const msg = err.message || "API request failed";
    // FastAPI often returns JSON like {"detail":"..."}; apiClient currently throws raw text.
    try {
      const parsed = JSON.parse(msg) as unknown;
      if (
        parsed &&
        typeof parsed === "object" &&
        "detail" in parsed &&
        typeof (parsed as { detail?: unknown }).detail === "string"
      ) {
        return (parsed as { detail: string }).detail;
      }
    } catch {
      // ignore JSON parse failures; keep original message
    }
    return msg;
  }
  return "API request failed";
}

function isPredictionValues(x: unknown): x is PredictionValues {
  if (!x || typeof x !== "object") return false;
  const o = x as Record<string, unknown>;
  const keys: (keyof PredictionValues)[] = [
    "malaria_risk_next_week",
    "ad_risk_next_week",
    "typhoid_risk_next_week",
    "avg_temperature",
    "avg_rainfall",
    "avg_humidity",
    "flood_inundation",
    "stagnant_water",
    "mean_ndvi",
  ];
  return keys.every((k) => typeof o[k] === "number" && Number.isFinite(o[k] as number));
}

function isExplanationImages(x: unknown): x is ExplanationImages {
  if (!x || typeof x !== "object") return false;
  const o = x as Record<string, unknown>;
  return typeof o.waterfall_plot === "string" && typeof o.bar_plot === "string";
}

function isDiseaseExplanations(x: unknown): x is DiseaseExplanations {
  if (!x || typeof x !== "object") return false;
  const o = x as Record<string, unknown>;
  return (
    isExplanationImages(o.malaria) &&
    isExplanationImages(o.ad) &&
    isExplanationImages(o.typhoid)
  );
}

function isPredictResponse(x: unknown): x is PredictResponse {
  if (!x || typeof x !== "object") return false;
  const o = x as Record<string, unknown>;
  const preds = o.predictions as unknown;
  return (
    typeof o.district_name === "string" &&
    typeof o.year === "number" &&
    typeof o.week_number === "number" &&
    isPredictionValues(preds) &&
    (preds &&
    typeof preds === "object" &&
    (!("explanations" in (preds as Record<string, unknown>)) ||
      isDiseaseExplanations((preds as Record<string, unknown>).explanations)))
  );
}

/**
 * Calls FastAPI `GET /predict`.
 *
 * Backend contract (query params):
 * - district_name (case-sensitive)
 * - year
 * - week_number
 */
export async function getPrediction(q: PredictQuery): Promise<PredictResponse> {
  const path = buildPredictPath(q);
  try {
    const data = await apiClient.get(path);
    if (!isPredictResponse(data)) {
      throw new Error("Unexpected response shape from /predict");
    }
    return data;
  } catch (err) {
    throw new Error(extractBackendErrorMessage(err));
  }
}

