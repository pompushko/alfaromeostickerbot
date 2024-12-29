import httpx
import asyncio
import re
import json
from typing import Optional, Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from datetime import datetime
from io import BytesIO

session_id = ""

headers = {
    'Content-Type': 'text/plain',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

cookies = {
    'DRIVE': '',
    'loginTypeCookie': 'UPRS',
    'EP_MKT': '023',
    'gig_bootstrap_4_orFmUKH1TrnP0kMf3hryrA': 'login-ra_ver4',
    'gig_llu': '',
    'gig_llp': '',
    'ga_NQRXPBM53J': 'GS1.1.1716315659.51.1.1716316203.0.0.0',
    'dtCookie': '',
    'AKA_A2': 'A',
    '_gid': 'GA1.2.924781583.1735413322',
    '_ga_7FSXK7VK1F': 'GS1.1.1735413329.64.1.1735413523.14.0.0',
    '_ga': 'GA1.2.1628127437.1702652518',
    'JSESSIONID': '',
    'EPERUIDC': '',
    'DWRSESSIONID': '',
    'LANGUAGE': '3',
    'GUI_LANG': '3',
    'EKV': ''
}

class FiatPartsClient:
    def __init__(self, headers: dict, cookies: dict):
        self.base_url = "https://eper.parts.fiat.com/dwr/call/plaincall"
        self.headers = headers
        self.cookies = cookies
        
    def _create_configuration_payload(self, vin: str, session_id: str) -> dict:
        return {
            'callCount': '1',
            'windowName': '',
            'c0-scriptName': 'MVSManager',
            'c0-methodName': 'getVinConfiguration',
            'c0-id': '0',
            'c0-param0': 'string:R',
            'c0-param1': 'string:3',
            'c0-param2': f'string:{vin}',
            'c0-param3': 'string:',
            'c0-param4': 'string:DEFAULT',
            'batchId': '1',
            'instanceId': '0',
            'page': '/navi?EU=1&COUNTRY=023&RMODE=DEFAULT&SBMK=R&MAKE=R&LANGUAGE=3&GUI_LANG=3&SAVE_PARAM=LANGUAGE',
            'scriptSessionId': session_id
        }
    
    def _create_alestimento_payload(self, catalog_code: str, vin: str, session_id: str) -> dict:
        return {
            'callCount': '1',
            'windowName': '',
            'c0-scriptName': 'MVSManager',
            'c0-methodName': 'getVinAlestimento',
            'c0-id': '0',
            'c0-param0': f'string:{catalog_code}',
            'c0-param1': 'string:3',
            'c0-param2': f'string:{vin}',
            'c0-param3': 'string:',
            'batchId': '1',
            'instanceId': '0',
            'page': '/navi?EU=1&COUNTRY=023&RMODE=DEFAULT&SBMK=R&MAKE=R&LANGUAGE=3&GUI_LANG=3&SAVE_PARAM=LANGUAGE',
            'scriptSessionId': session_id
        }

    def _parse_dwr_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        try:
            pattern = r'r\.handleCallback\("[^"]+",\s*"[^"]+",\s*(\[.*?\])\);'
            match = re.search(pattern, response_text)
            
            if match:
                json_str = match.group(1)
                
                json_str = json_str.replace("\\'", "'")
                
                json_str = re.sub(r'\\",', '",', json_str)
                
                json_str = re.sub(r'\\"}', '"}', json_str)
                
                json_str = re.sub(r'\\(?!["\\/bfnrt])', '', json_str)
                
                json_str = re.sub(r'([{,])\s*([a-zA-Z0-9_]+):', r'\1"\2":', json_str)
                
                try:
                    data = json.loads(json_str)
                    return data if data else None
                except json.JSONDecodeError as e:
                    print(f"Ошибка парсинга JSON после обработки: {e}")
                    print(f"На позиции {e.pos}:")
                    start = max(0, e.pos - 50)
                    end = min(len(json_str), e.pos + 50)
                    print(f"Контекст ошибки: ...{json_str[start:end]}...")
                    print(f"Полная строка JSON: {json_str}")  # Добавим для отладки
                    return None
                        
        except Exception as e:
            print(f"Общая ошибка парсинга: {e}")
            return None

    async def get_vin_configuration(self, vin: str, session_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/MVSManager.getVinConfiguration.dwr"
        payload = self._create_configuration_payload(vin, session_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, data=payload, cookies=self.cookies)
            return self._parse_dwr_response(response.text)

    async def get_vin_alestimento(self, catalog_code: str, vin: str, session_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/MVSManager.getVinAlestimento.dwr"
        payload = self._create_alestimento_payload(catalog_code, vin, session_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, data=payload, cookies=self.cookies)
            return self._parse_dwr_response(response.text)

    async def get_full_vin_info(self, vin: str, session_id: str) -> dict:
        config_data = await self.get_vin_configuration(vin, session_id)
        if not config_data:
            raise Exception("Не удалось получить конфигурацию VIN")

        catalog_code = config_data[0].get('catalogCode')
        if not catalog_code:
            raise Exception("Не удалось получить catalogCode из конфигурации")

        alestimento_data = await self.get_vin_alestimento(catalog_code, vin, session_id)
        
        return {
            "configuration": config_data,
            "alestimento": alestimento_data
        }

class FiatPartsPDFGenerator:
    def __init__(self):
        try:
            pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
        except:
            print("Шрифт Arial не найден, используем стандартный шрифт")

        self.styles = getSampleStyleSheet()
        self.style_header = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading1'],
            fontName='Arial',
            fontSize=14,
            spaceAfter=30,
            alignment=1
        )

    def create_pdf(self, data: dict) -> bytes:
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        elements = []
        
        title = Paragraph(f"Отчет по VIN: {data['configuration'][0].get('vin', 'Н/Д')}", self.style_header)
        elements.append(title)

        if data.get('configuration'):
            elements.extend(self._create_configuration_table(data['configuration']))

        if data.get('alestimento'):
            elements.extend(self._create_alestimento_table(data['alestimento']))

        doc.build(elements)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def _create_configuration_table(self, config_data):
        elements = []
        
        section_title = Paragraph("Конфигурация автомобиля", self.style_header)
        elements.append(section_title)

        table_data = []
        
        headers = ['Параметр', 'Значение']
        table_data.append(headers)

        if config_data and len(config_data) > 0:
            config = config_data[0]
            important_fields = [
                ('vin', 'VIN'),
                ('catalogCode', 'Код каталога'),
                ('model', 'Модель'),
                ('version', 'Версия'),
                ('engineCode', 'Код двигателя'),
                ('productionDate', 'Дата производства')
            ]
            
            for field, title in important_fields:
                if field in config:
                    table_data.append([title, str(config.get(field, 'Н/Д'))])

        table = Table(table_data, colWidths=[200, 300])
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Arial'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Arial'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('WORDWRAP', (0, 0), (-1, -1), True),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        return elements

    def _create_alestimento_table(self, alestimento_data):
        elements = []
        
        section_title = Paragraph("Дополнительная информация", self.style_header)
        elements.append(section_title)

        table_data = []
        headers = ['Код', 'Описание', 'Значение']
        table_data.append(headers)

        if isinstance(alestimento_data, list):
            for item in alestimento_data:
                if isinstance(item, dict):
                    code = item.get('code', 'Н/Д')
                    description = item.get('description', 'Н/Д')
                    value = item.get('value', 'Н/Д')
                    
                    description_paragraph = Paragraph(
                        description,
                        ParagraphStyle(
                            'Description',
                            parent=self.styles['Normal'],
                            fontSize=10,
                            leading=12,
                            wordWrap='CJK'
                        )
                    )
                    
                    table_data.append([code, description_paragraph, value])

        table = Table(
            table_data, 
            colWidths=[100, 300, 100],
            rowHeights=[30] + [None] * (len(table_data) - 1)
        )
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Arial'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Arial'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        return elements
