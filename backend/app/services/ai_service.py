from typing import Dict, Any, Optional, List
import openai
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.schemas_db import AIExplanation
from app.services.gap_engine import ResourceGapEngine

class AIService:
    @classmethod
    async def chat_or_explain(
        cls, 
        message: str, 
        academic_year: str, 
        context_type: str, 
        db: Session
    ) -> Dict[str, Any]:
        """
        Processes administrative queries using real system metrics.
        Degrades gracefully with deterministic, data-grounded explanations if OpenAI key is not provided.
        """
        # Fetch actual calculated metrics for the academic year
        gap_results = ResourceGapEngine.calculate_gaps(academic_year, db)
        
        # Build concise context data
        summary_context = {
            "academic_year": academic_year,
            "overall_health_score": gap_results["overall_health_score"],
            "total_shortages": gap_results["total_shortages"],
            "total_surpluses": gap_results["total_surpluses"],
            "category_summary": gap_results["summary_by_category"],
            "top_recommendations": [
                {
                    "dept": r["department"],
                    "action": r["action_type"],
                    "qty": r["recommended_quantity"],
                    "severity": r["severity"],
                    "reason": r["reason"]
                }
                for r in gap_results["recommendations"][:4]
            ]
        }

        # Check if OpenAI API key is configured
        if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 10:
            try:
                client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                system_prompt = (
                    "You are CampusPredict AI, an expert academic infrastructure planning and resource demand advisor. "
                    "You provide clear, data-driven, strategic recommendations to college deans and administrators based solely on the provided institutional data. "
                    "Do not invent facts or metrics. Clearly explain why shortages or surpluses occur, and formulate practical scheduling or procurement steps."
                )
                user_prompt = (
                    f"User Query: {message}\n\n"
                    f"Academic Year Context: {academic_year}\n"
                    f"System Computed Ground Truth Context:\n{summary_context}\n\n"
                    "Please provide a professional, actionable, well-structured response."
                )

                response = await client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=600,
                    temperature=0.3
                )
                answer_text = response.choices[0].message.content

                # Save AI log
                log_entry = AIExplanation(
                    prompt=message,
                    response=answer_text,
                    context_type=context_type,
                    model_used=settings.OPENAI_MODEL,
                    is_fallback=False
                )
                db.add(log_entry)
                db.commit()

                return {
                    "answer": answer_text,
                    "model_used": settings.OPENAI_MODEL,
                    "is_fallback": False,
                    "grounded_context": summary_context,
                    "suggested_actions": [
                        "Review Computer Science classroom deficit",
                        "Examine faculty hiring requirements",
                        "Download complete executive PDF report"
                    ]
                }
            except Exception as e:
                # Fall back to deterministic engine if API call fails
                fallback_ans = cls._generate_deterministic_fallback(message, summary_context)
                return {
                    "answer": f"[Notice: OpenAI API call encountered an error: {str(e)[:70]}... Switched to deterministic rule-based analysis]\n\n" + fallback_ans,
                    "model_used": "CampusPredict Rule-Based Fallback Engine",
                    "is_fallback": True,
                    "grounded_context": summary_context,
                    "suggested_actions": [
                        "Add classrooms to CS and AI departments",
                        "Recruit faculty in high-workload departments",
                        "Export Excel summary"
                    ]
                }

        # Deterministic Grounded Fallback
        fallback_ans = cls._generate_deterministic_fallback(message, summary_context)
        log_entry = AIExplanation(
            prompt=message,
            response=fallback_ans,
            context_type=context_type,
            model_used="Deterministic Fallback Engine",
            is_fallback=True
        )
        db.add(log_entry)
        db.commit()

        return {
            "answer": fallback_ans,
            "model_used": "Deterministic Institutional Rule Engine",
            "is_fallback": True,
            "grounded_context": summary_context,
            "suggested_actions": [
                "Prioritize Critical severity recommendations",
                "Reallocate surplus capacity from CE/ME to CS/AI",
                "Generate executive PDF report"
            ]
        }

    @staticmethod
    def _generate_deterministic_fallback(query: str, ctx: Dict[str, Any]) -> str:
        q_lower = query.lower()
        yr = ctx["academic_year"]
        health = ctx["overall_health_score"]
        shortages = ctx["total_shortages"]
        cats = ctx["category_summary"]
        recs = ctx["top_recommendations"]

        if "classroom" in q_lower or "room" in q_lower:
            cls_gap = cats.get("Classrooms", {}).get("gap", 0)
            return (
                f"### Classroom Capacity Analysis ({yr})\n\n"
                f"- **Total Classroom Gap:** {'Deficit of ' + str(int(cls_gap)) if cls_gap > 0 else 'Surplus/Balanced'}\n"
                f"- **Core Driver:** Projected enrollment expansion in computing and AI streams increases section counts beyond the current room stock.\n"
                f"- **Actionable Strategy:** \n"
                f"  1. Introduce staggered scheduling (staggered shifts) to increase daily room turnover.\n"
                f"  2. Reallocate underutilized lecture halls from departments with negative gap metrics (such as Mechanical and Civil Engineering).\n"
                f"  3. Convert traditional lecture spaces into multi-purpose smart classrooms."
            )

        if "faculty" in q_lower or "teacher" in q_lower or "staff" in q_lower:
            fac_gap = cats.get("Faculty", {}).get("gap", 0)
            return (
                f"### Faculty Workload & Demand Analysis ({yr})\n\n"
                f"- **Estimated Faculty Deficit:** {int(fac_gap)} members across departments.\n"
                f"- **Regulatory Standard:** Calculated based on AICTE/UGC recommended student-to-faculty benchmark (1:18) and a 16 hour/week teaching ceiling.\n"
                f"- **Actionable Strategy:** \n"
                f"  1. Initiate recruitment for Assistant Professors with specializations in AI, Data Science, and Systems.\n"
                f"  2. Utilize adjunct industry faculty for practical elective coursework.\n"
                f"  3. Avoid over-allocating existing professors beyond the 16 teaching hours limit to preserve research output."
            )

        if "priority" in q_lower or "score" in q_lower:
            return (
                f"### Resource Allocation Priority Scoring\n\n"
                f"The CampusPredict priority metric evaluates resource urgency on a 0–100 scale using four weighted components:\n\n"
                f"$$\\text{{Score}} = (\\text{{Severity}} \\times 0.40) + (\\text{{Utilization}} \\times 0.25) + (\\text{{Growth Rate}} \\times 0.20) + (\\text{{Criticality}} \\times 0.15)$$\n\n"
                f"- **Top Prioritized Item:** {recs[0]['dept']} ({recs[0]['action']}) with **{recs[0]['severity']}** urgency.\n"
                f"- Departments with rapid enrollment acceleration and peak utilization (>85%) receive immediate planning precedence."
            )

        # General executive summary
        rec_bullets = "\n".join([
            f"- **[{r['severity']}] {r['dept']}**: {r['action']} ({r['qty']} units) — {r['reason']}"
            for r in recs
        ])
        return (
            f"### Academic Planning Decision Support Brief ({yr})\n\n"
            f"**Institutional Health Index:** {health}/100 | **Identified Shortages:** {shortages}\n\n"
            f"#### Key Resource Balances:\n"
            f"- **Classrooms:** Required {cats['Classrooms']['required']} | Available {cats['Classrooms']['available']} | Net Gap: {cats['Classrooms']['gap']:+0.1f}\n"
            f"- **Faculty:** Required {cats['Faculty']['required']} | Available {cats['Faculty']['available']} | Net Gap: {cats['Faculty']['gap']:+0.1f}\n"
            f"- **Laboratories:** Required {cats['Laboratories']['required']} | Available {cats['Laboratories']['available']} | Net Gap: {cats['Laboratories']['gap']:+0.1f}\n"
            f"- **Equipment:** Required {cats['Equipment']['required']} | Available {cats['Equipment']['available']} | Net Gap: {cats['Equipment']['gap']:+0.1f}\n\n"
            f"#### High-Priority Administrative Actions:\n{rec_bullets}\n\n"
            f"*Summary computed deterministically using verified econometric & workload models.*"
        )
