CREATE TABLE IF NOT EXISTS messages (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    content TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE OR REPLACE FUNCTION add_message(p_id UUID, p_content TEXT)
RETURNS BIGINT AS $$
DECLARE
    v_message_id BIGINT;
BEGIN
    INSERT INTO messages (user_id, content)
    VALUES (p_id, p_content)
    RETURNING id INTO v_message_id;
    RETURN v_message_id;
END;
$$ LANGUAGE plpgsql;
DROP FUNCTION delete_message;
CREATE OR REPLACE FUNCTION delete_message(p_message_id BIGINT, p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM messages
    WHERE id = p_message_id AND user_id = p_user_id;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count > 0;
END;
$$ LANGUAGE plpgsql;