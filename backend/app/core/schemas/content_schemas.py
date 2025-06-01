# backend/app/core/schemas/content_schemas.py
from google.genai.types import Schema

# Master Context Schema
MASTER_CONTEXT_SCHEMA = Schema(
    type="object",
    properties={
        "core_concepts": Schema(
            type="array",
            items=Schema(type="string"),
            description="4-6 core concepts students must understand"
        ),
        "key_terminology": Schema(
            type="array",
            items=Schema(
                type="object",
                properties={
                    "term": Schema(type="string", description="The key term"),
                    "definition": Schema(type="string", description="Definition of the term")
                },
                required=["term", "definition"]
            ),
            description="5-8 key terms with precise definitions as an array of term-definition objects"
        ),
        "learning_objectives": Schema(
            type="array",
            items=Schema(type="string"),
            description="4-6 specific, measurable learning objectives"
        ),
        "difficulty_level": Schema(
            type="string",
            description="Difficulty level for this content"
        ),
        "grade_level": Schema(
            type="string",
            description="Target grade level for students"
        ),
        "prerequisites": Schema(
            type="array",
            items=Schema(type="string"),
            description="Required prerequisite knowledge"
        ),
        "real_world_applications": Schema(
            type="array",
            items=Schema(type="string"),
            description="3-5 real-world applications of this knowledge"
        )
    },
    required=["core_concepts", "key_terminology", "learning_objectives", "difficulty_level", "grade_level", "prerequisites", "real_world_applications"]
)

# Reading Content Schema
READING_CONTENT_SCHEMA = Schema(
    type="object",
    properties={
        "title": Schema(type="string", description="Title for the reading content"),
        "sections": Schema(
            type="array",
            items=Schema(
                type="object",
                properties={
                    "heading": Schema(type="string", description="Section heading"),
                    "content": Schema(type="string", description="Section content text"),
                    "key_terms_used": Schema(
                        type="array",
                        items=Schema(type="string"),
                        description="Key terms used in this section"
                    ),
                    "concepts_covered": Schema(
                        type="array",
                        items=Schema(type="string"),
                        description="Core concepts covered in this section"
                    )
                },
                required=["heading", "content", "key_terms_used", "concepts_covered"]
            )
        ),
        "word_count": Schema(type="integer", description="Estimated word count"),
        "reading_level": Schema(type="string", description="Appropriate reading level"),
        "grade_appropriate_features": Schema(
            type="array",
            items=Schema(type="string"),
            description="Features that make content appropriate for grade level"
        )
    },
    required=["title", "sections", "word_count", "reading_level", "grade_appropriate_features"]
)

# Visual Demo Metadata Schema
VISUAL_METADATA_SCHEMA = Schema(
    type="object",
    properties={
        "description": Schema(
            type="string",
            description="Clear description of what the visualization demonstrates and how it teaches the core concepts"
        ),
        "interactive_elements": Schema(
            type="array",
            items=Schema(type="string"),
            description="Specific interactive elements in the demo"
        ),
        "concepts_demonstrated": Schema(
            type="array",
            items=Schema(type="string"),
            description="Core concepts from master context that are demonstrated"
        ),
        "user_instructions": Schema(
            type="string",
            description="Simple, step-by-step instructions for students on how to interact with the demo"
        ),
        "grade_appropriate_features": Schema(
            type="array",
            items=Schema(type="string"),
            description="Features that make this demo engaging and appropriate for the grade level"
        ),
        "learning_objectives_addressed": Schema(
            type="array",
            items=Schema(type="string"),
            description="How each learning objective is demonstrated in the visualization"
        ),
        "educational_value": Schema(
            type="string",
            description="Explanation of how this demo reinforces the key terminology and concepts"
        )
    },
    required=["description", "interactive_elements", "concepts_demonstrated", "user_instructions", "grade_appropriate_features", "learning_objectives_addressed", "educational_value"]
)

# Practice Problems Schema
PRACTICE_PROBLEMS_SCHEMA = Schema(
    type="object",
    properties={
        "problems": Schema(
            type="array",
            items=Schema(
                type="object",
                properties={
                    "problem_type": Schema(type="string", description="Type of problem"),
                    "problem": Schema(type="string", description="The actual question/problem statement"),
                    "answer": Schema(type="string", description="The correct answer or solution"),
                    "success_criteria": Schema(
                        type="array",
                        items=Schema(type="string"),
                        description="Criteria that define successful completion"
                    ),
                    "teaching_note": Schema(type="string", description="Note for educators"),
                    "grade_level": Schema(type="string", description="Target grade level")
                },
                required=["problem_type", "problem", "answer", "success_criteria", "teaching_note", "grade_level"]
            )
        )
    },
    required=["problems"]
)