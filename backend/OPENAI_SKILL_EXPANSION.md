# OpenAI Skill Expansion Strategy

## Current Problem

O*NET has only **35 generic skills**:
- "Programming" (not Python, JavaScript, React, etc.)
- "Systems Analysis" (not Data Analysis, ML, etc.)
- Very high-level, doesn't capture modern tech skills

## Your Idea: Use OpenAI to Expand Skills

### Approach 1: Dynamic Skill Mapping (Recommended)
Use OpenAI to map user's specific skills to O*NET skills in real-time.

**Benefits:**
- Works with ANY user skill (Python, React, Kubernetes, etc.)
- No need to maintain a static mapping
- Understands context and relationships
- Can suggest multiple O*NET skills per user skill with confidence weights

**Implementation:**
```python
def expand_skill_with_openai(user_skill: str, all_onet_skills: List[str]) -> Dict[str, float]:
    """
    Use OpenAI to map a user skill to O*NET skills with confidence weights
    
    Returns: {"Programming": 0.9, "Systems Analysis": 0.7, ...}
    """
    prompt = f'''You're a career skills expert. Map this user skill to relevant O*NET skills.

User Skill: {user_skill}

Available O*NET Skills:
{', '.join(all_onet_skills)}

For each relevant O*NET skill, provide a confidence score (0.0-1.0).
Return ONLY valid JSON in this format:
{{
  "skill_name": confidence_score,
  ...
}}

Only include O*NET skills that are relevant (confidence > 0.3).'''
    
    # Call OpenAI and parse JSON response
    # Returns weighted mapping
```

### Approach 2: Semantic Similarity (Advanced)
Use OpenAI embeddings to find semantic similarity between user skills and O*NET skills.

**Benefits:**
- Very fast (cached embeddings)
- No API call per skill (batch process)
- Finds unexpected connections

**Implementation:**
```python
# 1. Pre-compute embeddings for all O*NET skills (once)
onet_embeddings = get_embeddings(all_onet_skills)

# 2. At runtime, get embedding for user skill
user_embedding = get_embedding(user_skill)

# 3. Find similar O*NET skills using cosine similarity
similarities = cosine_similarity(user_embedding, onet_embeddings)
```

### Approach 3: Hybrid (Best of Both)
1. Use static mapping for common skills (fast)
2. Use OpenAI for uncommon/new skills (accurate)
3. Cache OpenAI results for reuse

## Implementation Plan

### Phase 1: Add OpenAI Skill Expansion Service
Create `backend/services/skill_expansion_service.py`:

```python
class SkillExpansionService:
    def __init__(self):
        self.openai_service = OpenAIEnhancementService()
        self.cache = {}  # Cache expansions
        
    def expand_user_skills(
        self, 
        user_skills: List[str], 
        onet_skills: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        Expand each user skill to O*NET skills with weights
        
        Returns:
        {
            "Python": {"Programming": 0.9, "Systems Analysis": 0.7},
            "React": {"Programming": 0.8, "Technology Design": 0.6},
            ...
        }
        """
        expansions = {}
        for skill in user_skills:
            if skill in self.cache:
                expansions[skill] = self.cache[skill]
            else:
                expansion = self._expand_single_skill(skill, onet_skills)
                self.cache[skill] = expansion
                expansions[skill] = expansion
        return expansions
```

### Phase 2: Update Recommendation Service
Modify `build_user_feature_vector` to use expansions:

```python
def build_user_feature_vector(self, skills, ...):
    # Get O*NET skill expansions
    if skills:
        expansions = self.skill_expansion_service.expand_user_skills(
            skills, 
            all_skills
        )
        
        # Apply weighted expansions to skill vector
        for user_skill, onet_mappings in expansions.items():
            for onet_skill, weight in onet_mappings.items():
                idx = skill_lookup[onet_skill.lower()]
                skill_vector[idx] = max(
                    skill_vector[idx], 
                    weight * (importance / 5.0)
                )
```

### Phase 3: Optimize Performance
1. **Batch processing** - Expand all skills in one API call
2. **Persistent cache** - Save to Redis or file
3. **Fallback** - Use static mapping if OpenAI unavailable

## Expected Improvements

### Before (Static Mapping)
```
User Skills: ["Python", "Machine Learning", "React"]
O*NET Match: Programming (3 skills → 1 O*NET skill)
Score: 0.42 (Low)
```

### After (OpenAI Expansion)
```
User Skills: ["Python", "Machine Learning", "React"]
O*NET Mappings:
  - Python → Programming (0.9), Systems Analysis (0.7), Mathematics (0.5)
  - Machine Learning → Mathematics (0.9), Systems Analysis (0.8), Programming (0.7)
  - React → Programming (0.8), Technology Design (0.7)
  
Score: 0.87 (High)
Confidence: High
Better career matches: Data Scientists, ML Engineers, Software Developers
```

## Cost Considerations

### OpenAI API Costs
- **GPT-4**: ~$0.03 per 1K tokens
- **Embeddings**: ~$0.0001 per 1K tokens
- Average expansion: ~200 tokens = $0.006 per request

### Optimization Strategies
1. **Cache aggressively** - Most skills repeat
2. **Use embeddings** for common skills (cheaper)
3. **Batch process** - 5 skills at once
4. **Use GPT-3.5-turbo** - 10x cheaper, still accurate

### Cost Example
- 1000 users/day × 4 skills each = 4000 expansions
- With 80% cache hit rate = 800 API calls
- Cost: 800 × $0.006 = **$4.80/day** or **$144/month**
- With embeddings: **$0.40/month** (98% cheaper)

## Alternative: Expand O*NET Taxonomy

Instead of mapping TO O*NET, expand FROM O*NET:

1. Load O*NET skills
2. Use OpenAI to generate 10-20 modern equivalents per O*NET skill
3. Build a comprehensive skill taxonomy (350+ skills)
4. Match user skills against expanded taxonomy

**Example:**
```
O*NET: "Programming"
Expanded: 
  - Python, JavaScript, Java, C++, C#, Ruby, Go, Rust
  - React, Vue, Angular, Node.js, Django, Flask
  - Web Development, Mobile Development, Backend, Frontend
  - etc.
```

This is one-time cost, creates a rich skill database.

## Recommendation

**Start with Approach 1 (Dynamic Mapping)**:
1. Fast to implement
2. Works immediately
3. No database changes needed
4. Can add caching later

**Then optimize**:
1. Add caching (Redis or file-based)
2. Use embeddings for common skills
3. Consider expanding O*NET taxonomy for v2

## Implementation Priority

### High Priority (Do Now)
- ✅ Basic static mapping (already done in skill matching fix)
- 🔄 Add OpenAI skill expansion service
- 🔄 Update recommendation service to use it

### Medium Priority (Next Sprint)
- Cache expansion results
- Add embeddings for common skills
- Build skill synonym database

### Low Priority (Future)
- Expand O*NET taxonomy with OpenAI
- Multi-language support
- Industry-specific skill mappings

## Sample Code

See `backend/services/skill_expansion_service.py` (to be created)

## Testing

Before/After comparison:
1. Test with "Python, Machine Learning, React"
2. Check score improvement
3. Verify top recommendations
4. Monitor API costs


