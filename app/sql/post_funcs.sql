CREATE TABLE IF NOT EXISTS posts (
    id UUID  PRIMARY KEY DEFAULT gen_random_uuid(),
    userid UUID  NOT NULL  REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    caption TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);


CREATE OR REPLACE FUNCTION add_post(p_userid UUID, p_url TEXT, p_caption TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    post_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO post_count
    FROM posts
    WHERE userid = p_userid;

    IF post_count >= 5 THEN
        RAISE EXCEPTION 'User % has reached the limit of 5 posts', p_userid;
    END IF;

    INSERT INTO posts (userid, url, caption)
    VALUES (p_userid, p_url, p_caption);

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION change_user_profile_page_link(p_userid UUID, p_link TEXT)
RETURNS TABLE (id UUID, profile_page TEXT) AS $$
BEGIN
    RETURN QUERY
    UPDATE users
    SET profile_page = p_link
    WHERE users.id = p_userid
    RETURNING users.id, users.profile_page;
END;
$$ LANGUAGE plpgsql;
