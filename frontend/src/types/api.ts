export type User = {
  id: string;
  email: string;
  full_name: string | null;
  created_at: string;
};

export type Profile = {
  id: string;
  user_id: string;
  full_name: string | null;
  age_group: string | null;
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
};

export type DashboardSummary = {
  total_sessions: number;
  avg_capture_quality: number | null;
  latest_score: number | null;
  latest_band: string | null;
  recent_sessions: SessionDTO[];
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type RegisterPayload = {
  email: string;
  password: string;
  full_name?: string;
  age_group?: string;
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
  age_group: string;
  gender: string;
  height_cm: number | null;
  weight_kg: number | null;
  user_type: string;
  focus_area: string;
  self_reported_note: string;
}>;
