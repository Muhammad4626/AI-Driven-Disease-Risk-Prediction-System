import apiClient from "../api/apiClients";

export type CumulativeCasesResponse = {
  disease: string;
  total_cases: number;
};

export type PredictQuery = {
  district_name: string;
  year: number;
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
  local_explanations?: any;
  global_explanations?: any;
};

export type ExplanationImages = {
  /** Full data-URL, e.g. `data:image/png;base64,...` */
  waterfall: string;     // Changed from waterfall_plot
  /** Full data-URL, e.g. `data:image/png;base64,...` */
  bar: string;           // Changed from bar_plot
};

export type GlobalExplanationImages = {
  summary_plot: string;
  importance_bar: string;
};

export type DiseaseExplanations = {
  malaria: ExplanationImages;
  ad: ExplanationImages;
  typhoid: ExplanationImages;
};

export type GlobalDiseaseExplanations = {
  malaria: GlobalExplanationImages;
  ad: GlobalExplanationImages;
  typhoid: GlobalExplanationImages;
};

export type PredictionValuesWithExplanations = PredictionValues & {
  local_explanations?: DiseaseExplanations;        // New
  global_explanations?: GlobalDiseaseExplanations; // New
  // Keep old field for backward compatibility if needed
  explanations?: DiseaseExplanations;
};

export type PredictResponse = {
  district_name: string;
  year: number;
  week_number: number;
  predictions: PredictionValues;
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

  return `/api/predict?${params.toString()}`;
}

function extractBackendErrorMessage(err: unknown): string {
  if (err instanceof Error) {
    const msg = err.message || "API request failed";
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
      // ignore
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
  return typeof o.waterfall === "string" && typeof o.bar === "string";
}

function isGlobalExplanationImages(x: unknown): x is GlobalExplanationImages {
  if (!x || typeof x !== "object") return false;
  const o = x as Record<string, unknown>;
  return typeof o.summary_plot === "string" && typeof o.importance_bar === "string";
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

function isGlobalDiseaseExplanations(x: unknown): x is GlobalDiseaseExplanations {
  if (!x || typeof x !== "object") return false;
  const o = x as Record<string, unknown>;
  return (
    isGlobalExplanationImages(o.malaria) &&
    isGlobalExplanationImages(o.ad) &&
    isGlobalExplanationImages(o.typhoid)
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
    (preds && typeof preds === "object")
  );
}

/**
 * Calls FastAPI `GET /api/predict`.
 */

export async function getAllDistrictRisks() {
  const response = await apiClient.get("/api/districts/risks");
  return response.data;   // array of { district_name, adm2_pcode, risk_malaria, risk_diarrhea, risk_typhoid, ... }
}

export async function getCumulativeCases(disease: "malaria" | "typhoid" | "diarrhea" | "ad"): Promise<CumulativeCasesResponse> {
  return apiClient.get(`/api/summary/cases?disease=${encodeURIComponent(disease)}`);
}

// For TrendChart - Historical risk trend for a specific district
export async function getDistrictHistory(district_name: string, weeks_back: number = 12) {
  const response = await apiClient.get(
    `/api/districts/${encodeURIComponent(district_name)}/history?weeks_back=${weeks_back}`
  );
  return response.data;   // array of { week, risk_malaria, risk_diarrhea, risk_typhoid, ... }
}

// Main prediction endpoint
export async function getPrediction(q: PredictQuery): Promise<PredictResponse> {
  const params = new URLSearchParams({
    district_name: q.district_name,
    year: String(q.year),
    week_number: String(q.week_number),
  });

  const response = await apiClient.get(`/api/predict?${params.toString()}`);
  return response;
}

// export async function getPrediction(q: PredictQuery): Promise<PredictResponse> {
//   const path = buildPredictPath(q);
//   try {
//     const data = await apiClient.get(path);
//     if (!isPredictResponse(data)) {
//       throw new Error("Unexpected response shape from /predict");
//     }
//     return data;
//   } catch (err) {
//     throw new Error(extractBackendErrorMessage(err));
//   }
// }