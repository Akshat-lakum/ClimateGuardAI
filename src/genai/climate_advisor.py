"""
GenAI Layer - Climate Intelligence with RAG and LLM
CORRECTED VERSION: Uses new Google GenAI SDK (google.genai)
"""
import os
from typing import Dict, List, Optional
from loguru import logger
from pathlib import Path
import json

# Try importing both providers
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    logger.warning("Anthropic not installed")

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google GenAI not installed")

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader


class ClimateAdvisor:
    """GenAI-powered climate advisory system using Claude OR Gemini + RAG"""
    
    def __init__(
        self,
        api_key: str,
        provider: str = "gemini",
        chroma_persist_dir: str = "data/chroma_db",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize Climate Advisor
        
        Args:
            api_key: API key (Gemini or Claude)
            provider: "gemini" (FREE) or "claude"
            chroma_persist_dir: Directory for vector database
            embedding_model: Sentence transformer model name
        """
        self.provider = provider.lower()
        
        # Initialize LLM client
        if self.provider == "gemini":
            if not GEMINI_AVAILABLE:
                raise ImportError("Install google-genai: pip install google-genai")
            
            # Configure Gemini client with new SDK
            self.client = genai.Client(api_key=api_key)
            self.model_name = "gemini-2.5-flash"
            logger.info("Using Google Gemini (FREE)")
            
        elif self.provider == "claude":
            if not CLAUDE_AVAILABLE:
                raise ImportError("Install anthropic: pip install anthropic")
            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info("Using Claude Sonnet")
        else:
            raise ValueError("Provider must be 'gemini' or 'claude'")
        
        self.chroma_persist_dir = chroma_persist_dir
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'}
        )
        
        # Initialize or load vector store
        self.vectorstore = None
        self._load_or_create_vectorstore()
        
        logger.info(f"ClimateAdvisor initialized with {self.provider}")
    
    def _load_or_create_vectorstore(self):
        """Load existing vectorstore or create new one"""
        try:
            if Path(self.chroma_persist_dir).exists():
                self.vectorstore = Chroma(
                    persist_directory=self.chroma_persist_dir,
                    embedding_function=self.embeddings
                )
                logger.info("Loaded existing vector store")
            else:
                self.vectorstore = Chroma(
                    persist_directory=self.chroma_persist_dir,
                    embedding_function=self.embeddings
                )
                logger.info("Created new vector store")
        except Exception as e:
            logger.error(f"Error with vector store: {e}")
            raise
    
    def index_climate_documents(self, documents_dir: str):
        """
        Index climate reports and documents
        
        Args:
            documents_dir: Directory containing PDF/text documents
        """
        try:
            documents_path = Path(documents_dir)
            all_documents = []
            
            # Load PDFs
            for pdf_file in documents_path.glob("**/*.pdf"):
                loader = PyPDFLoader(str(pdf_file))
                documents = loader.load()
                all_documents.extend(documents)
                logger.info(f"Loaded {pdf_file.name}")
            
            # Load text files
            for txt_file in documents_path.glob("**/*.txt"):
                loader = TextLoader(str(txt_file))
                documents = loader.load()
                all_documents.extend(documents)
                logger.info(f"Loaded {txt_file.name}")
            
            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            
            splits = text_splitter.split_documents(all_documents)
            
            # Add to vector store
            self.vectorstore.add_documents(splits)
            self.vectorstore.persist()
            
            logger.info(f"Indexed {len(splits)} document chunks")
            
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            raise
    
    def retrieve_relevant_context(
        self,
        query: str,
        k: int = 5
    ) -> List[str]:
        """
        Retrieve relevant context from knowledge base
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            
        Returns:
            List of relevant text chunks
        """
        try:
            results = self.vectorstore.similarity_search(query, k=k)
            contexts = [doc.page_content for doc in results]
            return contexts
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    def generate_climate_advisory(
        self,
        location: Dict,
        weather_forecast: Dict,
        satellite_data: Dict,
        historical_events: List[Dict] = None
    ) -> Dict:
        """
        Generate comprehensive climate advisory using Gemini or Claude
        
        Args:
            location: Location info (name, lat, lon)
            weather_forecast: Weather predictions
            satellite_data: Satellite indices (NDVI, NDWI, temperature)
            historical_events: Past climate events in region
            
        Returns:
            Advisory with recommendations
        """
        try:
            # Build context from data
            context = self._build_context(
                location,
                weather_forecast,
                satellite_data,
                historical_events
            )
            
            # Retrieve relevant knowledge
            query = f"Climate risks and adaptation for {location.get('name')} with temperature {weather_forecast.get('median', [0])[0]}°C"
            relevant_docs = self.retrieve_relevant_context(query, k=3)
            
            # Construct prompt
            prompt = self._construct_advisory_prompt(context, relevant_docs)
            
            # Call LLM based on provider
            if self.provider == "gemini":
                response_text = self._call_gemini(prompt)
            else:
                response_text = self._call_claude(prompt)
            
            # Parse response into structured format
            advisory = self._parse_advisory_response(response_text)
            
            logger.info(f"Generated advisory for {location.get('name')}")
            return advisory
            
        except Exception as e:
            logger.error(f"Error generating advisory: {e}")
            return {"error": str(e)}
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API using new SDK"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def _call_claude(self, prompt: str) -> str:
        """Call Claude API"""
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
    
    def _build_context(
        self,
        location: Dict,
        weather_forecast: Dict,
        satellite_data: Dict,
        historical_events: List[Dict]
    ) -> str:
        """Build context string from input data"""
        
        context_parts = [
            f"Location: {location.get('name', 'Unknown')}",
            f"Coordinates: {location.get('lat')}, {location.get('lon')}",
            "",
            "Weather Forecast (7-day):",
            f"- Median Temperature: {weather_forecast.get('median', [])}",
            f"- Temperature Range: {weather_forecast.get('lower_bound', [])} to {weather_forecast.get('upper_bound', [])}",
            "",
            "Satellite Data:",
            f"- NDVI (Vegetation Health): {satellite_data.get('ndvi', {}).get('mean', 'N/A')}",
            f"- NDWI (Water Availability): {satellite_data.get('ndwi', {}).get('mean', 'N/A')}",
            f"- Land Surface Temperature: {satellite_data.get('temperature_celsius', {}).get('mean', 'N/A')}°C",
        ]
        
        if historical_events:
            context_parts.append("")
            context_parts.append("Historical Climate Events:")
            for event in historical_events[:3]:
                context_parts.append(f"- {event.get('type', 'Event')}: {event.get('description', '')}")
        
        return "\n".join(context_parts)
    
    def _construct_advisory_prompt(
        self,
        context: str,
        relevant_docs: List[str]
    ) -> str:
        """Construct prompt for LLM"""
        
        knowledge_base = "\n\n".join([f"Reference {i+1}: {doc}" for i, doc in enumerate(relevant_docs)])
        
        prompt = f"""You are a climate intelligence advisor helping farmers and local authorities make informed decisions.

Current Situation:
{context}

Relevant Climate Knowledge:
{knowledge_base}

Based on this information, provide a comprehensive advisory with the following sections:

1. RISK ASSESSMENT (rate: Low/Medium/High)
   - Temperature stress risks
   - Water availability concerns
   - Extreme weather probability

2. IMMEDIATE ACTIONS (next 7 days)
   - Specific recommendations for farmers
   - Water management strategies
   - Crop protection measures

3. CROP RECOMMENDATIONS
   - Suitable crops for current conditions
   - Crops to avoid
   - Alternative varieties

4. DISASTER PREPAREDNESS
   - Early warning signs to watch
   - Mitigation strategies
   - Emergency contacts/resources

5. LONG-TERM ADAPTATION
   - Sustainable practices
   - Climate-resilient strategies

Format your response as clear, actionable bullet points in each section. Be specific and practical."""

        return prompt
    
    def _parse_advisory_response(self, response: str) -> Dict:
        """Parse LLM response into structured format"""
        
        sections = {
            'risk_assessment': '',
            'immediate_actions': '',
            'crop_recommendations': '',
            'disaster_preparedness': '',
            'long_term_adaptation': '',
            'full_text': response
        }
        
        # Split by section headers
        current_section = None
        for line in response.split('\n'):
            line = line.strip()
            
            if 'RISK ASSESSMENT' in line.upper():
                current_section = 'risk_assessment'
            elif 'IMMEDIATE ACTIONS' in line.upper():
                current_section = 'immediate_actions'
            elif 'CROP RECOMMENDATIONS' in line.upper():
                current_section = 'crop_recommendations'
            elif 'DISASTER PREPAREDNESS' in line.upper():
                current_section = 'disaster_preparedness'
            elif 'LONG-TERM ADAPTATION' in line.upper() or 'LONG TERM' in line.upper():
                current_section = 'long_term_adaptation'
            elif current_section and line:
                sections[current_section] += line + '\n'
        
        return sections
    
    def generate_voice_advisory(
        self,
        advisory: Dict,
        language: str = "en"
    ) -> str:
        """
        Generate simplified voice-friendly advisory
        
        Args:
            advisory: Structured advisory
            language: Language code (en, hi, mr, etc.)
            
        Returns:
            Voice-friendly text
        """
        try:
            prompt = f"""Convert this climate advisory into a simple, conversational voice message in {language} language.
Use simple words, short sentences, and a friendly tone suitable for farmers.

Advisory:
{advisory.get('full_text', '')}

Voice Message (in {language}, but write in English script if not English):"""

            if self.provider == "gemini":
                return self._call_gemini(prompt)
            else:
                return self._call_claude(prompt)
            
        except Exception as e:
            logger.error(f"Error generating voice advisory: {e}")
            return "Unable to generate voice advisory."


# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Use Gemini (FREE!)
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    advisor = ClimateAdvisor(
        api_key=gemini_key,
        provider="gemini",
        chroma_persist_dir="data/chroma_db"
    )
    
    # Sample data
    location = {"name": "Nashik, Maharashtra", "lat": 19.9975, "lon": 73.7898}
    
    weather_forecast = {
        "median": [32, 33, 34, 33, 32, 31, 30],
        "lower_bound": [28, 29, 30, 29, 28, 27, 26],
        "upper_bound": [36, 37, 38, 37, 36, 35, 34]
    }
    
    satellite_data = {
        "ndvi": {"mean": 0.45},
        "ndwi": {"mean": 0.22},
        "temperature_celsius": {"mean": 35.5}
    }
    
    historical_events = [
        {"type": "Drought", "description": "2019 drought affected 30% of cropland"}
    ]
    
    advisory = advisor.generate_climate_advisory(
        location, weather_forecast, satellite_data, historical_events
    )
    
    print("Climate Advisory:")
    print(json.dumps(advisory, indent=2))