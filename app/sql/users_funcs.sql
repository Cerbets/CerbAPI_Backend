CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    profile_page TEXT DEFAULT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);


CREATE OR REPLACE FUNCTION register_user(p_email TEXT, p_password TEXT)
RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
BEGIN
    INSERT INTO users (email, hashed_password)
    VALUES (p_email, p_password)
    RETURNING id INTO v_user_id;

    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_user_for_login(p_email TEXT)
RETURNS TABLE (id UUID, hashed_password TEXT,profile_page TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT users.id, users.hashed_password , users.profile_page
    FROM users
    WHERE email = p_email;
END;
$$ LANGUAGE plpgsql;



