-- Lost & Found Portal Database Schema for Supabase
-- Run this in your Supabase SQL Editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types/enums
CREATE TYPE item_type AS ENUM ('lost', 'found');
CREATE TYPE item_category AS ENUM ('electronics', 'bags', 'jewelry', 'clothing', 'personal', 'books', 'sports', 'other');
CREATE TYPE urgency_level AS ENUM ('low', 'medium', 'high');
CREATE TYPE item_status AS ENUM ('active', 'claimed', 'resolved', 'archived');
CREATE TYPE claim_status AS ENUM ('pending', 'approved', 'rejected', 'completed');

-- Profiles table (extends Supabase auth.users)
CREATE TABLE profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    phone TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Items table (main table for lost and found items)
CREATE TABLE items (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    type item_type NOT NULL,
    title TEXT NOT NULL CHECK (length(title) >= 3 AND length(title) <= 200),
    description TEXT NOT NULL CHECK (length(description) >= 10),
    category item_category NOT NULL,
    location TEXT NOT NULL CHECK (length(location) >= 2),
    date_lost DATE,
    time_lost TEXT,
    images TEXT[] DEFAULT '{}',
    reward INTEGER DEFAULT 0 CHECK (reward >= 0),
    urgency urgency_level DEFAULT 'medium',
    status item_status DEFAULT 'active',
    contact_preference TEXT DEFAULT 'email' CHECK (contact_preference IN ('email', 'phone')),
    view_count INTEGER DEFAULT 0,
    flagged BOOLEAN DEFAULT FALSE,
    flag_reason TEXT,
    moderation_status TEXT CHECK (moderation_status IN ('pending', 'approved', 'rejected', 'flagged', 'under_review')),
    moderated_by UUID REFERENCES profiles(id),
    moderated_at TIMESTAMP WITH TIME ZONE,
    moderation_notes TEXT,
    verification_status TEXT DEFAULT 'unverified' CHECK (verification_status IN ('unverified', 'verified', 'disputed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Claim requests table
CREATE TABLE claim_requests (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    item_id UUID REFERENCES items(id) ON DELETE CASCADE NOT NULL,
    claimer_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    message TEXT NOT NULL CHECK (length(message) >= 10),
    evidence_urls TEXT[],
    status claim_status DEFAULT 'pending',
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    admin_notes TEXT,
    processed_by UUID REFERENCES profiles(id),
    processed_at TIMESTAMP WITH TIME ZONE,
    contact_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Prevent duplicate claims from same user for same item
    UNIQUE(item_id, claimer_id)
);

-- NEW: Disputes table for conflict resolution
CREATE TABLE disputes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    item_id UUID REFERENCES items(id) ON DELETE CASCADE NOT NULL,
    owner_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('ownership_dispute', 'false_claim', 'multiple_claims', 'verification_issue')),
    description TEXT NOT NULL,
    status TEXT DEFAULT 'investigating' CHECK (status IN ('investigating', 'pending_review', 'escalated', 'resolved', 'closed')),
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    assigned_to UUID REFERENCES profiles(id), -- Admin assigned to case
    resolution TEXT,
    admin_notes TEXT,
    evidence_urls TEXT[],
    involved_parties JSONB, -- Array of user IDs and their roles
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dispute participants junction table
CREATE TABLE dispute_participants (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    dispute_id UUID REFERENCES disputes(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('claimant', 'witness', 'reporter')),
    evidence_provided TEXT,
    statement TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notifications table
CREATE TABLE notifications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('item_claimed', 'claim_approved', 'claim_rejected', 'item_found_match', 'item_moderated', 'dispute_created', 'dispute_resolved', 'admin_message')),
    read BOOLEAN DEFAULT FALSE,
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    action_url TEXT, -- Deep link to relevant page
    related_item_id UUID REFERENCES items(id),
    related_claim_id UUID REFERENCES claim_requests(id),
    related_dispute_id UUID REFERENCES disputes(id),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- NEW: Admin actions audit log
CREATE TABLE admin_actions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    admin_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    action TEXT NOT NULL, -- approve, reject, flag, remove, bulk_approve, etc.
    content_type TEXT NOT NULL, -- item, claim, user, dispute
    content_id TEXT NOT NULL, -- Can be single ID or comma-separated for bulk actions
    target_user_id UUID REFERENCES profiles(id), -- User affected by action
    notes TEXT,
    metadata JSONB, -- Additional context (old values, etc.)
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- NEW: Content reports table
CREATE TABLE content_reports (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    reporter_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    content_type TEXT NOT NULL CHECK (content_type IN ('item', 'claim', 'user', 'comment')),
    content_id UUID NOT NULL,
    reason TEXT NOT NULL CHECK (reason IN ('spam', 'inappropriate', 'fraud', 'stolen_goods', 'false_information', 'harassment', 'other')),
    description TEXT,
    evidence_urls TEXT[],
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'investigating', 'resolved', 'dismissed')),
    severity TEXT DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    reviewed_by UUID REFERENCES profiles(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- NEW: Platform analytics table
CREATE TABLE analytics_events (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    event_type TEXT NOT NULL, -- user_registration, item_posted, claim_made, item_resolved, etc.
    user_id UUID REFERENCES profiles(id),
    item_id UUID REFERENCES items(id),
    metadata JSONB,
    session_id TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance (fixed duplicates)
CREATE INDEX idx_items_type ON items(type);
CREATE INDEX idx_items_category ON items(category);
CREATE INDEX idx_items_status ON items(status);
CREATE INDEX idx_items_user_id ON items(user_id);
CREATE INDEX idx_items_created_at ON items(created_at DESC);
CREATE INDEX idx_items_flagged ON items(flagged) WHERE flagged = true;
CREATE INDEX idx_items_location_text ON items USING gin(to_tsvector('english', location));
CREATE INDEX idx_items_search ON items USING gin(to_tsvector('english', title || ' ' || description));

CREATE INDEX idx_claim_requests_item_id ON claim_requests(item_id);
CREATE INDEX idx_claim_requests_claimer_id ON claim_requests(claimer_id);
CREATE INDEX idx_claim_requests_status ON claim_requests(status);

CREATE INDEX idx_disputes_status ON disputes(status);
CREATE INDEX idx_disputes_priority ON disputes(priority);
CREATE INDEX idx_disputes_item_id ON disputes(item_id);
CREATE INDEX idx_disputes_assigned_to ON disputes(assigned_to);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(read);
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, read) WHERE read = false;

CREATE INDEX idx_admin_actions_admin_id ON admin_actions(admin_id);
CREATE INDEX idx_admin_actions_content_type ON admin_actions(content_type);
CREATE INDEX idx_admin_actions_created_at ON admin_actions(created_at DESC);

CREATE INDEX idx_analytics_events_type_date ON analytics_events(event_type, created_at);
CREATE INDEX idx_analytics_events_user_id ON analytics_events(user_id);

-- Enable Row Level Security (RLS)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE items ENABLE ROW LEVEL SECURITY;
ALTER TABLE claim_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE disputes ENABLE ROW LEVEL SECURITY;
ALTER TABLE dispute_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_reports ENABLE ROW LEVEL SECURITY;

-- RLS Policies for profiles
CREATE POLICY "Users can view all profiles" ON profiles FOR SELECT USING (true);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON profiles FOR INSERT WITH CHECK (auth.uid() = id);

-- RLS Policies for items
CREATE POLICY "Anyone can view active items" ON items FOR SELECT USING (
    status IN ('active', 'claimed') OR user_id = auth.uid()
);
CREATE POLICY "Users can insert own items" ON items FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own items" ON items FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Admins can update any item" ON items FOR UPDATE USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)
);

-- RLS Policies for claim_requests
CREATE POLICY "Users can view claims for their items or claims they made" ON claim_requests FOR SELECT USING (
    claimer_id = auth.uid() OR 
    item_id IN (SELECT id FROM items WHERE user_id = auth.uid()) OR
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)
);
CREATE POLICY "Users can create claims" ON claim_requests FOR INSERT WITH CHECK (auth.uid() = claimer_id);
CREATE POLICY "Item owners can update claim status" ON claim_requests FOR UPDATE USING (
    item_id IN (SELECT id FROM items WHERE user_id = auth.uid()) OR
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)
);

-- RLS Policies for notifications
CREATE POLICY "Users can view own notifications" ON notifications FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own notifications" ON notifications FOR UPDATE USING (auth.uid() = user_id);

-- RLS Policies for disputes
CREATE POLICY "Users can view disputes they're involved in" ON disputes FOR SELECT USING (
    owner_id = auth.uid()
    OR assigned_to = auth.uid()
    OR EXISTS (
        SELECT 1 FROM dispute_participants 
        WHERE dispute_participants.dispute_id = disputes.id 
        AND dispute_participants.user_id = auth.uid()
    )
    OR EXISTS (
        SELECT 1 FROM profiles 
        WHERE profiles.id = auth.uid() 
        AND profiles.is_admin = true
    )
);
CREATE POLICY "Admins can manage all disputes" ON disputes FOR ALL USING (
    EXISTS (
        SELECT 1 FROM profiles 
        WHERE profiles.id = auth.uid() 
        AND profiles.is_admin = true
    )
);

-- RLS Policies for admin actions
CREATE POLICY "Admins can view all admin actions" ON admin_actions FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM profiles 
        WHERE profiles.id = auth.uid() 
        AND profiles.is_admin = true
    )
);
CREATE POLICY "Admins can insert admin actions" ON admin_actions FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM profiles 
        WHERE profiles.id = auth.uid() 
        AND profiles.is_admin = true
    )
);

-- RLS Policies for content reports
CREATE POLICY "Users can view own reports" ON content_reports FOR SELECT USING (
    reporter_id = auth.uid()
    OR EXISTS (
        SELECT 1 FROM profiles 
        WHERE profiles.id = auth.uid() 
        AND profiles.is_admin = true
    )
);
CREATE POLICY "Authenticated users can create reports" ON content_reports FOR INSERT WITH CHECK (auth.uid() = reporter_id);

-- Functions and triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_items_updated_at BEFORE UPDATE ON items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_claim_requests_updated_at BEFORE UPDATE ON claim_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_disputes_updated_at BEFORE UPDATE ON disputes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to log analytics events
CREATE OR REPLACE FUNCTION log_analytics_event(
    p_event_type TEXT,
    p_user_id UUID DEFAULT NULL,
    p_item_id UUID DEFAULT NULL,
    p_metadata JSONB DEFAULT NULL
)
RETURNS void AS $$
BEGIN
    INSERT INTO analytics_events (event_type, user_id, item_id, metadata)
    VALUES (p_event_type, p_user_id, p_item_id, p_metadata);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'full_name');
    
    -- Log analytics event
    PERFORM log_analytics_event('user_registration', NEW.id, NULL, 
        json_build_object('email_domain', split_part(NEW.email, '@', 2))::jsonb);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to automatically create profile on signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to increment view count
CREATE OR REPLACE FUNCTION increment_item_view_count(item_uuid UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE items 
    SET view_count = view_count + 1 
    WHERE id = item_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to create notification
CREATE OR REPLACE FUNCTION create_notification(
    p_user_id UUID,
    p_title TEXT,
    p_message TEXT,
    p_type TEXT,
    p_priority TEXT DEFAULT 'normal',
    p_related_item_id UUID DEFAULT NULL,
    p_related_claim_id UUID DEFAULT NULL,
    p_related_dispute_id UUID DEFAULT NULL,
    p_action_url TEXT DEFAULT NULL,
    p_expires_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    notification_id UUID;
BEGIN
    INSERT INTO notifications (
        user_id, title, message, type, priority,
        related_item_id, related_claim_id, related_dispute_id,
        action_url, expires_at
    )
    VALUES (
        p_user_id, p_title, p_message, p_type, p_priority,
        p_related_item_id, p_related_claim_id, p_related_dispute_id,
        p_action_url, p_expires_at
    )
    RETURNING id INTO notification_id;
    
    RETURN notification_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to auto-flag suspicious content
CREATE OR REPLACE FUNCTION check_suspicious_content()
RETURNS TRIGGER AS $$
BEGIN
    -- Flag items with suspicious characteristics
    IF NEW.title ILIKE '%iPhone%' AND NEW.title ILIKE '%found%' AND NEW.reward > 100 THEN
        NEW.flagged = true;
        NEW.flag_reason = 'High-value electronics with large reward - potential fraud';
        NEW.moderation_status = 'under_review';
    END IF;
    
    -- Flag items from unverified users posting multiple high-value items
    IF EXISTS (
        SELECT 1 FROM items 
        WHERE user_id = NEW.user_id 
        AND reward > 50 
        AND created_at > NOW() - INTERVAL '24 hours'
        GROUP BY user_id 
        HAVING COUNT(*) >= 3
    ) THEN
        NEW.flagged = true;
        NEW.flag_reason = 'Multiple high-value items posted in short timeframe';
        NEW.moderation_status = 'under_review';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auto-flagging suspicious content
CREATE TRIGGER check_suspicious_content_trigger
    BEFORE INSERT ON items
    FOR EACH ROW EXECUTE FUNCTION check_suspicious_content();

-- Storage bucket for item images
INSERT INTO storage.buckets (id, name, public) 
VALUES ('item-images', 'item-images', true)
ON CONFLICT (id) DO NOTHING;

-- Storage policy for item images
CREATE POLICY "Anyone can view item images" ON storage.objects FOR SELECT USING (bucket_id = 'item-images');
CREATE POLICY "Authenticated users can upload item images" ON storage.objects FOR INSERT WITH CHECK (
    bucket_id = 'item-images' AND auth.role() = 'authenticated'
);
CREATE POLICY "Users can update own item images" ON storage.objects FOR UPDATE USING (
    bucket_id = 'item-images' AND auth.uid()::text = (storage.foldername(name))[1]
);
CREATE POLICY "Users can delete own item images" ON storage.objects FOR DELETE USING (
    bucket_id = 'item-images' AND auth.uid()::text = (storage.foldername(name))[1]
); 