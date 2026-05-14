"""
Professional Sentiment Analysis Service
Sử dụng ensemble Deep Learning models
"""

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    text: str
    sentiment: str  # positive, negative, neutral
    confidence: float
    confidence_level: str  # high, medium, low, very_high
    keywords: List[str]


class ProfessionalSentimentAnalyzer:
    """Enterprise-grade sentiment analyzer"""
    
    def __init__(self):
        self.device = 0 if torch.cuda.is_available() else -1
        self.models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize multiple professional models"""
        logger.info("Loading professional sentiment models...")
        
        # Model 1: DistilBERT for English
        try:
            self.models['general'] = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=self.device
            )
            logger.info("✓ General sentiment model loaded")
        except Exception as e:
            logger.error(f"Failed to load general model: {e}")
        
        # Model 2: Multilingual for Vietnamese
        try:
            self.models['multilingual'] = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                device=self.device
            )
            logger.info("✓ Multilingual sentiment model loaded")
        except Exception as e:
            logger.error(f"Failed to load multilingual model: {e}")
        
        # Model 3: FinBERT for financial
        try:
            self.models['financial'] = pipeline(
                "text-classification",
                model="ProsusAI/finbert",
                device=self.device
            )
            logger.info("✓ Financial sentiment model loaded")
        except Exception as e:
            logger.warning(f"FinBERT not available (optional): {e}")
    
    def analyze_professional(self, text: str, max_length: int = 512) -> SentimentResult:
        """Analyze sentiment using ensemble of models"""
        if not text or len(text.strip()) < 3:
            return SentimentResult(
                text=text,
                sentiment="neutral",
                confidence=0.0,
                confidence_level="low",
                keywords=[]
            )
        
        text = text[:max_length]
        results = {}
        
        # Run models
        if 'general' in self.models:
            try:
                result = self.models['general'](text)[0]
                results['general'] = {
                    'label': result['label'].lower(),
                    'score': result['score']
                }
            except Exception as e:
                logger.warning(f"General model error: {e}")
        
        if 'multilingual' in self.models:
            try:
                result = self.models['multilingual'](text)[0]
                label = result['label'].lower()
                if 'positive' in label or 'love' in label or '5' in label:
                    label = 'positive'
                elif 'negative' in label or 'hate' in label or '1' in label:
                    label = 'negative'
                else:
                    label = 'neutral'
                
                results['multilingual'] = {
                    'label': label,
                    'score': result['score']
                }
            except Exception as e:
                logger.warning(f"Multilingual model error: {e}")
        
        final_sentiment = self._aggregate_predictions(results)
        confidence = self._calculate_ensemble_confidence(results)
        keywords = self._extract_keywords(text)
        
        return SentimentResult(
            text=text,
            sentiment=final_sentiment['label'],
            confidence=confidence,
            confidence_level=self._get_confidence_level(confidence),
            keywords=keywords
        )
    
    def _aggregate_predictions(self, results: Dict) -> Dict:
        """Aggregate predictions using voting"""
        if not results:
            return {'label': 'neutral', 'score': 0.5}
        
        predictions = {}
        for model_name, result in results.items():
            label = result['label']
            predictions[label] = predictions.get(label, 0) + result['score']
        
        best_label = max(predictions.items(), key=lambda x: x[1])
        
        return {
            'label': best_label[0],
            'score': best_label[1] / len(results)
        }
    
    def _calculate_ensemble_confidence(self, results: Dict) -> float:
        """Calculate ensemble confidence"""
        if not results:
            return 0.0
        
        scores = [r['score'] for r in results.values()]
        return float(np.mean(scores))
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Map confidence to readable level"""
        if confidence >= 0.85:
            return "very_high"
        elif confidence >= 0.70:
            return "high"
        elif confidence >= 0.55:
            return "medium"
        else:
            return "low"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract sentiment keywords"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'wonderful',
                         'tuyệt vời', 'tốt', 'xuất sắc', 'yêu thích', 'dễ thương']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'horrible', 'poor',
                         'tệ', 'ghê tởm', 'kinh khủng', 'tồi tệ', 'chán']
        
        text_lower = text.lower()
        keywords = []
        
        for word in positive_words + negative_words:
            if word in text_lower:
                keywords.append(word)
        
        return list(set(keywords))[:5]
    
    def batch_analyze(self, texts: List[str]) -> List[SentimentResult]:
        """Analyze multiple texts"""
        return [self.analyze_professional(text) for text in texts]


class StrategicInsightGenerator:
    """Generate strategic insights from sentiment analysis"""
    
    @staticmethod
    def generate_insights(analysis_results: List[SentimentResult], 
                         total_comments: int) -> Dict:
        """Generate strategic insights"""
        if not analysis_results:
            return {
                'overall_sentiment': 'neutral',
                'trend': 'stable',
                'risks': [],
                'opportunities': [],
                'recommendations': []
            }
        
        positive_count = sum(1 for r in analysis_results if r.sentiment == 'positive')
        negative_count = sum(1 for r in analysis_results if r.sentiment == 'negative')
        neutral_count = sum(1 for r in analysis_results if r.sentiment == 'neutral')
        
        positive_pct = positive_count / len(analysis_results) * 100 if analysis_results else 0
        negative_pct = negative_count / len(analysis_results) * 100 if analysis_results else 0
        
        avg_confidence = np.mean([r.confidence for r in analysis_results])
        
        # Determine overall sentiment
        if positive_pct >= 60:
            overall = 'very_positive'
        elif positive_pct >= 45:
            overall = 'positive'
        elif negative_pct >= 45:
            overall = 'negative'
        elif negative_pct >= 60:
            overall = 'very_negative'
        else:
            overall = 'mixed'
        
        risks = StrategicInsightGenerator._identify_risks(
            analysis_results, negative_pct
        )
        opportunities = StrategicInsightGenerator._identify_opportunities(
            analysis_results, positive_pct
        )
        recommendations = StrategicInsightGenerator._generate_recommendations(
            overall, negative_pct, avg_confidence
        )
        
        return {
            'overall_sentiment': overall,
            'positive_pct': round(positive_pct, 1),
            'negative_pct': round(negative_pct, 1),
            'neutral_pct': round(neutral_count / len(analysis_results) * 100, 1),
            'average_confidence': round(avg_confidence, 3),
            'trend': StrategicInsightGenerator._determine_trend(positive_pct, negative_pct),
            'risks': risks,
            'opportunities': opportunities,
            'recommendations': recommendations,
            'confidence_distribution': {
                'very_high': sum(1 for r in analysis_results if r.confidence >= 0.85),
                'high': sum(1 for r in analysis_results if 0.70 <= r.confidence < 0.85),
                'medium': sum(1 for r in analysis_results if 0.55 <= r.confidence < 0.70),
                'low': sum(1 for r in analysis_results if r.confidence < 0.55),
            }
        }
    
    @staticmethod
    def _determine_trend(positive_pct: float, negative_pct: float) -> str:
        """Determine sentiment trend"""
        if positive_pct > negative_pct:
            return "positive"
        elif negative_pct > positive_pct:
            return "negative"
        else:
            return "stable"
    
    @staticmethod
    def _identify_risks(results: List[SentimentResult], negative_pct: float) -> List[Dict]:
        """Identify risks"""
        risks = []
        
        if negative_pct >= 40:
            risks.append({
                'type': 'high_negative_sentiment',
                'severity': 'high' if negative_pct >= 50 else 'medium',
                'description': f'{negative_pct:.1f}% of comments are negative',
                'impact': 'Brand reputation, customer retention'
            })
        
        negative_results = [r for r in results if r.sentiment == 'negative']
        if negative_results:
            all_keywords = []
            for r in negative_results:
                all_keywords.extend(r.keywords)
            
            if all_keywords:
                risks.append({
                    'type': 'key_complaints',
                    'severity': 'medium',
                    'description': f'Common complaint themes: {", ".join(set(all_keywords)[:3])}',
                    'impact': 'Product/service quality issues'
                })
        
        return risks
    
    @staticmethod
    def _identify_opportunities(results: List[SentimentResult], positive_pct: float) -> List[Dict]:
        """Identify opportunities"""
        opportunities = []
        
        if positive_pct >= 60:
            opportunities.append({
                'type': 'strong_positive_sentiment',
                'potential': 'high',
                'description': f'{positive_pct:.1f}% of customers express positive sentiment',
                'action': 'Leverage positive sentiment for marketing & testimonials'
            })
        
        if positive_pct >= 40 and positive_pct < 60:
            opportunities.append({
                'type': 'growth_potential',
                'potential': 'medium',
                'description': 'Balanced feedback shows areas for improvement',
                'action': 'Focus on converting neutral customers to positive'
            })
        
        return opportunities
    
    @staticmethod
    def _generate_recommendations(overall: str, negative_pct: float, avg_confidence: float) -> List[Dict]:
        """Generate recommendations"""
        recommendations = []
        
        if negative_pct >= 40:
            recommendations.append({
                'priority': 'high',
                'action': 'Conduct root cause analysis',
                'details': 'Investigate why customers express negative sentiment',
                'timeline': 'Within 1-2 weeks',
                'owner': 'Customer Service & Product Team'
            })
            
            recommendations.append({
                'priority': 'high',
                'action': 'Implement response strategy',
                'details': 'Create action plan to address top complaints',
                'timeline': 'Within 2-4 weeks',
                'owner': 'Management'
            })
        
        if avg_confidence < 0.70:
            recommendations.append({
                'priority': 'medium',
                'action': 'Manual review of low-confidence cases',
                'details': f'Review comments with confidence < 70%',
                'timeline': 'Ongoing',
                'owner': 'Analysis Team'
            })
        
        if overall in ['very_positive', 'positive']:
            recommendations.append({
                'priority': 'medium',
                'action': 'Amplify positive brand messaging',
                'details': 'Use positive feedback in marketing materials',
                'timeline': 'Ongoing',
                'owner': 'Marketing Team'
            })
        
        return recommendations
