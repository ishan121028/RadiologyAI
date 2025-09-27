#!/usr/bin/env python3

"""
CriticalAlert AI MCP Client Example

Shows how to interact with the CriticalAlert AI MCP server
following the latest Pathway MCP client patterns.
"""

import asyncio
import logging
from fastmcp import Client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MCP Server URL (matching the server configuration)
CRITICAL_ALERT_MCP_URL = "http://localhost:8127/mcp/"

async def test_radiology_analysis():
    """Test radiology report analysis tool"""
    
    print("🏥 Testing Radiology Analysis Tool")
    print("=" * 40)
    
    client = Client(CRITICAL_ALERT_MCP_URL)
    
    try:
        async with client:
            # Test with a simulated critical finding
            test_report = {
                "report_content": """
                FINDINGS: Large filling defect is noted in the main pulmonary artery 
                extending into both right and left main pulmonary arteries, consistent 
                with pulmonary embolism. There is evidence of right heart strain with 
                enlarged right ventricle.
                
                IMPRESSION: Massive pulmonary embolism with signs of right heart strain.
                Immediate medical attention required.
                """,
                "patient_id": "PATIENT_12345",
                "urgency_level": "EMERGENCY"
            }
            
            print(f"📋 Analyzing report for patient: {test_report['patient_id']}")
            
            result = await client.call_tool(
                name="analyze_radiology_report",
                arguments=test_report
            )
            
            print("✅ Analysis Results:")
            print(f"   🚨 Alert Level: {result.get('alert_level', 'N/A')}")
            print(f"   🔍 Critical Conditions: {result.get('critical_conditions', [])}")
            print(f"   📝 Findings Summary: {result.get('findings_summary', 'N/A')[:100]}...")
            print(f"   ⚡ Immediate Actions: {len(result.get('immediate_actions', []))} actions")
            print(f"   💊 Treatment Recommendations: {len(result.get('treatment_recommendations', []))} recommendations")
            
            return result
            
    except Exception as e:
        print(f"❌ Error testing radiology analysis: {e}")
        return None


async def test_active_alerts_monitoring():
    """Test active alerts monitoring tool"""
    
    print("\n🚨 Testing Active Alerts Monitoring")
    print("=" * 40)
    
    client = Client(CRITICAL_ALERT_MCP_URL)
    
    try:
        async with client:
            # Query for RED level alerts
            alert_query = {
                "alert_level": "RED",
                "time_range_hours": 24
            }
            
            print("🔍 Querying for RED level alerts in last 24 hours...")
            
            result = await client.call_tool(
                name="get_active_alerts",
                arguments=alert_query
            )
            
            print("✅ Active Alerts:")
            print(f"   📊 Alert ID: {result.get('alert_id', 'N/A')}")
            print(f"   🚨 Level: {result.get('alert_level', 'N/A')}")
            print(f"   👤 Patient: {result.get('patient_id', 'N/A')}")
            print(f"   🏥 Condition: {result.get('condition', 'N/A')}")
            print(f"   📅 Timestamp: {result.get('timestamp', 'N/A')}")
            print(f"   ⏱️  Response Time: {result.get('response_time_minutes', 'N/A')} minutes")
            
            return result
            
    except Exception as e:
        print(f"❌ Error testing active alerts: {e}")
        return None


async def test_alert_statistics():
    """Test alert statistics tool"""
    
    print("\n📊 Testing Alert Statistics")
    print("=" * 40)
    
    client = Client(CRITICAL_ALERT_MCP_URL)
    
    try:
        async with client:
            print("📈 Retrieving system statistics...")
            
            result = await client.call_tool(
                name="get_alert_statistics",
                arguments={}
            )
            
            print("✅ System Statistics:")
            print(f"   📋 Total Reports Processed: {result.get('total_reports_processed', 'N/A')}")
            print(f"   🔴 RED Alerts Today: {result.get('red_alerts_today', 'N/A')}")
            print(f"   🟠 ORANGE Alerts Today: {result.get('orange_alerts_today', 'N/A')}")
            print(f"   🟡 YELLOW Alerts Today: {result.get('yellow_alerts_today', 'N/A')}")
            print(f"   🟢 GREEN Reports Today: {result.get('green_reports_today', 'N/A')}")
            print(f"   ⚡ Avg Processing Time: {result.get('avg_processing_time_seconds', 'N/A')}s")
            print(f"   ⏱️  Avg Response Time: {result.get('avg_response_time_minutes', 'N/A')} min")
            print(f"   🟢 System Status: {result.get('system_status', 'N/A')}")
            
            return result
            
    except Exception as e:
        print(f"❌ Error testing statistics: {e}")
        return None


async def test_medical_recommendations():
    """Test medical recommendations tool"""
    
    print("\n💊 Testing Medical Recommendations")
    print("=" * 40)
    
    client = Client(CRITICAL_ALERT_MCP_URL)
    
    try:
        async with client:
            # Test with emergency findings
            recommendation_request = {
                "findings": "Massive pulmonary embolism with right heart strain",
                "patient_context": "65-year-old male post-operative day 3 from hip replacement",
                "urgency": "EMERGENCY"
            }
            
            print("🩺 Generating medical recommendations for emergency case...")
            
            result = await client.call_tool(
                name="generate_medical_recommendations",
                arguments=recommendation_request
            )
            
            print("✅ Medical Recommendations:")
            print(f"   🔍 Findings: {result.get('findings', 'N/A')}")
            print(f"   🚨 Urgency Level: {result.get('urgency_level', 'N/A')}")
            print(f"   📋 Recommendations:")
            for i, rec in enumerate(result.get('recommendations', []), 1):
                print(f"      {i}. {rec}")
            print(f"   🎯 Next Steps:")
            for i, step in enumerate(result.get('next_steps', []), 1):
                print(f"      {i}. {step}")
            
            return result
            
    except Exception as e:
        print(f"❌ Error testing medical recommendations: {e}")
        return None


async def run_complete_mcp_demo():
    """Run complete MCP server demo"""
    
    print("🚨 CriticalAlert AI MCP Client Demo")
    print("=" * 50)
    print(f"🔗 Connecting to: {CRITICAL_ALERT_MCP_URL}")
    print()
    
    # Test all MCP tools
    analysis_result = await test_radiology_analysis()
    alerts_result = await test_active_alerts_monitoring()
    stats_result = await test_alert_statistics()
    recommendations_result = await test_medical_recommendations()
    
    print("\n🎯 Demo Summary")
    print("=" * 20)
    print(f"✅ Radiology Analysis: {'✓' if analysis_result else '✗'}")
    print(f"✅ Active Alerts: {'✓' if alerts_result else '✗'}")
    print(f"✅ Alert Statistics: {'✓' if stats_result else '✗'}")
    print(f"✅ Medical Recommendations: {'✓' if recommendations_result else '✗'}")
    
    if all([analysis_result, alerts_result, stats_result, recommendations_result]):
        print("\n🎉 All MCP tools working successfully!")
        print("🏥 CriticalAlert AI MCP server is fully operational")
    else:
        print("\n⚠️  Some MCP tools encountered errors")
        print("🔧 Check server logs and configuration")


async def main():
    """Main client example"""
    
    try:
        await run_complete_mcp_demo()
    except ConnectionError:
        print("❌ Cannot connect to MCP server")
        print("🚀 Start the server with: python src/mcp/critical_alert_mcp_server.py")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🏥 CriticalAlert AI MCP Client")
    print("Make sure the MCP server is running on localhost:8127")
    print()
    
    asyncio.run(main())
