# Example: How to Update Pricing

## If you want to change the Starter Package price from $299 to $399:

### Step 1: Edit the file
```bash
nano knowledge_base/services/pricing_packages.md
```

### Step 2: Find and update the line:
```markdown
# Change this:
### **Starter Package - $299/month**

# To this:
### **Starter Package - $399/month**
```

### Step 3: Re-ingest knowledge base:
```bash
python3 ingest_knowledge_base.py
```

### Step 4: Deploy to production:
```bash
git add knowledge_base/
git commit -m "💰 Updated Starter Package pricing to $399"
git push origin main
```

### Step 5: Test the change:
Send WhatsApp message: "What are your pricing packages?"
The bot should now respond with the updated $399 price.

## That's it! The RAG system will automatically use the updated information. 