export interface Profile {
  id: string;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  user_type: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ProfileUpdate {
  first_name?: string | null;
  last_name?: string | null;
}
