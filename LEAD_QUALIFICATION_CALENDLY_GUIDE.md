# 🎯 Lead Qualification & Calendly Integration System

## Overview

The **Lead Qualification & Calendly Integration System** is an AI-powered feature that automatically analyzes user messages to identify qualified business leads and sends them personalized Calendly discovery call invitations. This system works alongside the existing handover system to create a complete lead management workflow.

## 🚀 How It Works

### **1. AI-Powered Lead Analysis**
When a user sends a message, the system:
- ✅ **Analyzes business intent** using OpenAI GPT-3.5-turbo
- ✅ **Scores lead quality** from 0-100 points
- ✅ **Identifies buying signals** and business indicators
- ✅ **Provides confidence ratings** for decision making

### **2. Smart Lead Qualification**
The AI looks for these key indicators:

#### **🎯 Business Intent Signals**
- Looking for business solutions/services
- Asking about pricing, packages, or business plans
- Mentioning business problems or challenges
- Discussing implementation, integration, or adoption
- Questions like "how does this work for business"

#### **💰 Buying Signals**
- Timeline questions ("when can we start", "how long does it take")
- Budget-related inquiries
- Decision-making language ("we need", "looking for")
- Comparison shopping ("vs competitors")
- Implementation questions

#### **🏢 Business Context**
- Mentions company size, industry, or role
- Discusses team needs or requirements
- References current tools/systems
- Talks about scaling or growth

#### **🔥 Engagement Level**
- Asks detailed questions
- Shows genuine interest beyond basic info
- Responds with specific use cases
- Provides context about their situation

### **3. Automatic Calendly Integration**
When a qualified lead is detected:
- ✅ **Personalized invitation** based on lead quality (HIGH/MEDIUM/LOW)
- ✅ **Professional messaging** with clear value proposition
- ✅ **Calendly link** automatically included
- ✅ **CRM updates** with lead scoring and activity logging

## 📊 Lead Quality Classifications

### **🔥 HIGH Quality (80-100 points)**
- Strong business intent + clear buying signals + high engagement
- **Gets**: Personalized professional invitation with specific value props
- **Priority**: High priority in CRM
- **Response**: "Great to connect with a fellow business professional!"

### **⚡ MEDIUM Quality (60-79 points)**
- Some business indicators + decent engagement
- **Gets**: Friendly invitation focusing on understanding needs
- **Priority**: Medium priority in CRM
- **Response**: "Thanks for your interest in our business solutions!"

### **💡 LOW Quality (40-59 points)**
- Limited business context or buying signals
- **Gets**: Simple invitation for consultation
- **Priority**: Standard follow-up
- **Response**: "Thank you for your interest!"

### **❌ NOT QUALIFIED (0-39 points)**
- No business intent or engagement indicators
- **Gets**: No Calendly invitation
- **Action**: Continue with normal bot conversation

## 🛠️ Configuration

### **Environment Variables**

Add these to your `.env` file:

```bash
# Lead Qualification Settings
LEAD_QUALIFICATION_ENABLED=true
LEAD_QUALIFICATION_CONFIDENCE_THRESHOLD=0.75
LEAD_QUALIFICATION_MODEL=gpt-3.5-turbo
LEAD_QUALIFICATION_LOGGING_ENABLED=true

# Calendly Integration
CALENDLY_DISCOVERY_CALL_URL=https://calendly.com/your-company/discovery-call
CALENDLY_AUTO_SEND_ENABLED=true

# Lead Scoring
QUALIFIED_LEAD_MIN_SCORE=70
DISCOVERY_CALL_LEAD_SCORE_BOOST=30
```

### **Key Settings Explained**

- **`LEAD_QUALIFICATION_CONFIDENCE_THRESHOLD=0.75`**: AI must be 75% confident before qualifying a lead
- **`QUALIFIED_LEAD_MIN_SCORE=70`**: Lead must score 70+ points to be qualified
- **`DISCOVERY_CALL_LEAD_SCORE_BOOST=30`**: Qualified leads get +30 points in CRM
- **`CALENDLY_DISCOVERY_CALL_URL`**: Your actual Calendly scheduling link

## 📋 Database Setup

Run the migration to set up required tables:

```bash
# Apply the database migration
psql -d your_database -f database_migration_lead_qualification.sql
```

This creates:
- ✅ **`lead_qualification_log`** table for AI analysis logging
- ✅ **Enhanced `contacts`** table with discovery call tracking
- ✅ **Enhanced `lead_details`** table with qualification metadata
- ✅ **Analytics views** for monitoring performance

## 🎯 Message Processing Flow

Here's how the system integrates with your existing WhatsApp bot:

```
1. User sends message
   ↓
2. Check for handover request (existing)
   ↓ (if no handover needed)
3. 🆕 LEAD QUALIFICATION ANALYSIS
   ↓
4. If qualified → Send Calendly + Update CRM
   ↓
5. Continue with normal bot response
```

### **Integration Points**

The lead qualification happens:
- **After** handover detection (handover takes priority)
- **Before** normal bot response
- **Parallel** to conversation flow (doesn't interrupt user experience)
- **With context** from conversation history for better analysis

## 📱 User Experience Examples

### **Example 1: HIGH Quality Lead**
**User**: *"Hi, we're a 50-person marketing agency looking for a WhatsApp automation solution. We're currently using basic tools but need something more robust for client communication. What's your pricing for business plans?"*

**AI Analysis**:
- Business intent: ✅ (business solution, pricing)
- Buying signals: ✅ (specific use case, current tools)
- Business context: ✅ (company size, industry)
- Engagement: ✅ (detailed question)
- **Score**: 92/100 → **HIGH quality**

**Auto Response**:
```
🎯 Great to connect with a fellow business professional!

Based on our conversation, I can see you're exploring business solutions. I'd love to discuss how we can specifically help with your needs.

Let's schedule a quick 15-minute discovery call:
https://calendly.com/your-company/discovery-call

During this call, we'll:
✅ Understand your specific requirements
✅ Discuss potential solutions
✅ Explore how we can add value to your business
✅ Answer any questions you have

No pressure, just a friendly conversation about your business goals!

Looking forward to speaking with you! 🚀
```

### **Example 2: NOT Qualified**
**User**: *"What's this?"*

**AI Analysis**:
- Business intent: ❌ (too vague)
- Buying signals: ❌ (none)
- Business context: ❌ (none)
- Engagement: ❌ (minimal)
- **Score**: 15/100 → **NOT QUALIFIED**

**Result**: No Calendly invitation, continues with normal bot response.

## 📊 CRM Integration

### **Lead Scoring Updates**
- ✅ **+30 points** for qualified leads
- ✅ **Lead status** updated to "hot"
- ✅ **Discovery call requested** flag set
- ✅ **Business indicators** and buying signals stored

### **Activity Logging**
- ✅ **Lead qualification activity** with AI analysis details
- ✅ **Calendly invitation activity** when link is sent
- ✅ **Full metadata** including confidence scores and reasoning

### **Contact Updates**
- ✅ **Last qualification date** timestamp
- ✅ **Discovery call requested** boolean flag
- ✅ **Lead source** marked as "whatsapp_qualification"

## 🔍 Monitoring & Analytics

### **Real-time Monitoring**
Query lead qualification performance:

```sql
-- Daily lead qualification stats
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_analyzed,
    SUM(CASE WHEN final_decision THEN 1 ELSE 0 END) as qualified_count,
    AVG(confidence_score) as avg_confidence,
    AVG(lead_score) as avg_score
FROM lead_qualification_log 
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### **Lead Quality Distribution**
```sql
-- Lead quality breakdown
SELECT 
    lead_quality,
    COUNT(*) as count,
    AVG(confidence_score) as avg_confidence
FROM lead_qualification_log 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY lead_quality
ORDER BY avg_confidence DESC;
```

### **Calendly Invitation Success Rate**
```sql
-- Discovery call invitation tracking
SELECT 
    COUNT(DISTINCT contact_id) as qualified_leads,
    SUM(CASE WHEN latest_calendly_activity IS NOT NULL THEN 1 ELSE 0 END) as calendly_sent
FROM qualified_leads_summary;
```

## 🎛️ Fine-tuning the System

### **Adjusting Sensitivity**

**More Aggressive (Qualify More Leads)**:
```bash
LEAD_QUALIFICATION_CONFIDENCE_THRESHOLD=0.6  # Lower threshold
QUALIFIED_LEAD_MIN_SCORE=60                   # Lower score requirement
```

**More Conservative (Qualify Fewer, Higher-Quality Leads)**:
```bash
LEAD_QUALIFICATION_CONFIDENCE_THRESHOLD=0.85  # Higher threshold
QUALIFIED_LEAD_MIN_SCORE=80                    # Higher score requirement
```

### **Custom Calendly Messages**

Edit the messages in `lead_qualification_service.py`:
- Modify the `send_calendly_discovery_call()` function
- Customize messages for each lead quality level
- Add industry-specific messaging

### **Business Indicator Customization**

Modify the AI prompt in `analyze_lead_qualification_ai()` to:
- Add industry-specific indicators
- Include product-specific buying signals
- Adjust for your business model

## 🚨 Troubleshooting

### **Issue**: No Calendly invitations being sent
**Solutions**:
- Check `CALENDLY_AUTO_SEND_ENABLED=true`
- Verify `CALENDLY_DISCOVERY_CALL_URL` is correct
- Check OpenAI API key is valid
- Review confidence threshold settings

### **Issue**: Too many/few leads being qualified
**Solutions**:
- Adjust `LEAD_QUALIFICATION_CONFIDENCE_THRESHOLD`
- Modify `QUALIFIED_LEAD_MIN_SCORE`
- Review AI prompt for your business context
- Check recent qualification logs for patterns

### **Issue**: AI analysis failing
**Solutions**:
- Verify OpenAI API key and credits
- Check internet connectivity
- Review error logs for specific issues
- Ensure `LEAD_QUALIFICATION_ENABLED=true`

## 🔮 Advanced Features

### **A/B Testing Calendly Messages**
Track which message variants perform better:
```python
# Add message variant tracking to metadata
'message_variant': 'professional_v1',
'calendly_click_tracking': 'utm_source=whatsapp&utm_campaign=auto_qualification'
```

### **Integration with CRM Pipelines**
Automatically move qualified leads through sales stages:
```python
# Add to lead processing
if lead_quality == 'HIGH':
    # Move to "Discovery Call Scheduled" stage
    update_crm_stage(contact_id, 'discovery_scheduled')
```

### **Multi-language Support**
Extend AI prompts for different languages:
```python
# Detect language and use appropriate prompts
if detected_language == 'spanish':
    prompt = spanish_lead_qualification_prompt
```

## 📈 Success Metrics

Track these KPIs to measure system effectiveness:

1. **Lead Qualification Rate**: % of messages that result in qualified leads
2. **Calendly Click Rate**: % of sent invitations that get clicked
3. **Meeting Booking Rate**: % of Calendly clicks that book meetings
4. **Qualified Lead Conversion**: % of qualified leads that become customers
5. **AI Accuracy**: Manual review of AI qualification decisions

## 🎯 Best Practices

### **For Sales Teams**
- ✅ **Quick follow-up** on high-quality leads within 1 hour
- ✅ **Personalized outreach** using stored business indicators
- ✅ **Context awareness** from qualification trigger messages

### **For Marketing Teams**
- ✅ **Monitor qualification patterns** to understand customer language
- ✅ **A/B test Calendly messages** for better conversion
- ✅ **Use business indicators** for targeted content creation

### **For Product Teams**
- ✅ **Analyze buying signals** to understand feature priorities
- ✅ **Review qualification logs** for product-market fit insights
- ✅ **Track conversation patterns** for UX improvements

---

**🚀 Ready to Get Started?**

1. **Set up environment variables** with your Calendly URL
2. **Run the database migration** to create required tables
3. **Test with sample business queries** to verify functionality
4. **Monitor lead qualification logs** for fine-tuning
5. **Start booking discovery calls** with qualified leads!

**Next Steps**: Integrate with your sales team's workflow and start converting qualified WhatsApp leads into booked discovery calls! 📅✨ 