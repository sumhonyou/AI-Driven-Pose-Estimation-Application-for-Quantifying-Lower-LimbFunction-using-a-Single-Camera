export type User = {
  id: string;
  email: string;
  full_name: string | null;
  avatar_image: string | null;
  created_at: string;
};

export type Profile = {
  id: string;
  user_id: string;
  full_name: string | null;
  avatar_image: string | null;
  exact_age: number | null;
  gender: string | null;
  height_cm: number | null;
  weight_kg: number | null;
  user_type: string | null;
  focus_area: string | null;
  self_reported_note: string | null;
  created_at: string;
  updated_at: string;
};

export type Exercise = {
  id: string;
  code: string;
  name: string;
  mode: "functional" | "rehab" | string;
  description: string | null;
  view_guidance: string | null;
  is_active: boolean;
};

export type SessionDTO = {
  id: string;
  mode: "functional" | "rehab" | string;
  exercise_code: string;
  exercise_name: string;
  exercise_type: string;
  started_at: string;
  ended_at: string | null;
  status: string;
  capture_quality: number | null;
  valid_frame_ratio: number | null;
  score: number | null;
  band: "good" | "fair" | "poor" | string | null;
  // null for exercises with no rep concept (SLS, WBLT) and for sessions
  // recorded before this field existed.
  rep_count: number | null;
};

export type ExerciseLatest = {
  score: number | null;
  band: string | null;
  capture_quality: number | null;
};

export type DashboardSummary = {
  total_sessions: number;
  avg_capture_quality: number | null;
  latest_score: number | null;
  latest_band: string | null;
  recent_sessions: SessionDTO[];
  // Keyed by exercise_type, e.g. { sit_to_stand: {...}, squat: {...} }.
  latest: Record<string, ExerciseLatest>;
};

export type TrendPoint = {
  session_id: string;
  date: string;
  score: number | null;
  band: string | null;
  capture_quality: number | null;
  // Module B only; always null for Module A exercise types.
  confidence: number | null;
};

export type ExerciseTrend = {
  points: TrendPoint[];
  mdc: number | null;
  mdc_source: "published" | "none";
};

// Keyed by exercise_type; only types the account has sessions for are present.
export type DashboardTrends = Record<string, ExerciseTrend>;

export type DashboardErrorTag = {
  tag_code: string;
  severity: string | null;
  count: number;
};

// Keyed by exercise_type; Module B types only (Module A is absent, not empty).
export type DashboardErrorTags = Record<string, DashboardErrorTag[]>;

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type RegisterPayload = {
  email: string;
  password: string;
  full_name?: string;
  exact_age?: number;
  gender?: string;
  user_type?: string;
  focus_area?: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type ProfileUpdatePayload = Partial<{
  full_name: string;
  avatar_image: string | null;
  exact_age: number | null;
  gender: string;
  height_cm: number | null;
  weight_kg: number | null;
  user_type: string;
  focus_area: string;
  self_reported_note: string;
}>;
