#!/usr/bin/env python3

import pymysql
from backend.config import get_db_connection

# Language code to name mapping (common Wikipedia languages)
LANGUAGE_NAMES = {
    'ab': 'Abkhazian', 'ace': 'Acehnese', 'ady': 'Adyghe', 'af': 'Afrikaans',
    'als': 'Alemannic', 'alt': 'Southern Altai', 'am': 'Amharic', 'ami': 'Amis',
    'ang': 'Old English', 'ann': 'Obolo', 'anp': 'Angika', 'arc': 'Aramaic',
    'ary': 'Moroccan Arabic', 'atj': 'Atikamekw', 'av': 'Avar', 'avk': 'Kotava',
    'awa': 'Awadhi', 'ay': 'Aymara', 'ba': 'Bashkir', 'ban': 'Balinese',
    'bat-smg': 'Samogitian', 'bbc': 'Batak Toba', 'bcl': 'Central Bikol',
    'bdr': 'West Coast Bajau', 'be-tarask': 'Belarusian (Taraškievica)',
    'bew': 'Betawi', 'bg': 'Bulgarian', 'bh': 'Bhojpuri', 'bi': 'Bislama',
    'bjn': 'Banjar', 'blk': "Pa'O", 'bm': 'Bambara', 'bn': 'Bengali',
    'bo': 'Tibetan', 'bpy': 'Bishnupriya', 'btm': 'Batak Mandailing',
    'bug': 'Buginese', 'bxr': 'Russia Buriat', 'cbk-zam': 'Chavacano',
    'cdo': 'Min Dong Chinese', 'ce': 'Chechen', 'ch': 'Chamorro',
    'chr': 'Cherokee', 'chy': 'Cheyenne', 'ckb': 'Central Kurdish',
    'co': 'Corsican', 'cr': 'Cree', 'crh': 'Crimean Tatar', 'csb': 'Kashubian',
    'cu': 'Church Slavonic', 'cv': 'Chuvash', 'cy': 'Welsh', 'dag': 'Dagbani',
    'dga': 'Dagaare', 'din': 'Dinka', 'diq': 'Zazaki', 'dsb': 'Lower Sorbian',
    'dtp': 'Central Dusun', 'dty': 'Doteli', 'dv': 'Dhivehi', 'dz': 'Dzongkha',
    'ee': 'Ewe', 'eml': 'Emilian-Romagnol', 'eu': 'Basque', 'ext': 'Extremaduran',
    'fa': 'Persian', 'fat': 'Fanti', 'ff': 'Fula', 'fiu-vro': 'Võro',
    'fj': 'Fijian', 'fo': 'Faroese', 'fon': 'Fon', 'frp': 'Arpitan',
    'frr': 'Northern Frisian', 'fur': 'Friulian', 'fy': 'West Frisian',
    'ga': 'Irish', 'gag': 'Gagauz', 'gan': 'Gan Chinese', 'gcr': 'Guianan Creole',
    'gd': 'Scottish Gaelic', 'glk': 'Gilaki', 'gn': 'Guarani', 'gom': 'Goan Konkani',
    'gor': 'Gorontalo', 'got': 'Gothic', 'gpe': 'Ghanaian Pidgin',
    'guc': 'Wayuu', 'gur': 'Farefare', 'guw': 'Gun', 'gv': 'Manx',
    'ha': 'Hausa', 'hak': 'Hakka Chinese', 'haw': 'Hawaiian', 'hif': 'Fiji Hindi',
    'hsb': 'Upper Sorbian', 'ht': 'Haitian Creole', 'hy': 'Armenian',
    'hyw': 'Western Armenian', 'ia': 'Interlingua', 'iba': 'Iban',
    'ie': 'Interlingue', 'ig': 'Igbo', 'igl': 'Igala', 'ik': 'Inupiaq',
    'ilo': 'Iloko', 'inh': 'Ingush', 'io': 'Ido', 'is': 'Icelandic',
    'iu': 'Inuktitut', 'jam': 'Jamaican Patois', 'jbo': 'Lojban', 'jv': 'Javanese',
    'kaa': 'Kara-Kalpak', 'kab': 'Kabyle', 'kbd': 'Kabardian', 'kbp': 'Kabiye',
    'kcg': 'Tyap', 'kg': 'Kongo', 'kge': 'Komering', 'ki': 'Kikuyu',
    'kk': 'Kazakh', 'km': 'Khmer', 'kn': 'Kannada', 'knc': 'Central Kanuri',
    'koi': 'Komi-Permyak', 'krc': 'Karachay-Balkar', 'ks': 'Kashmiri',
    'ksh': 'Colognian', 'ku': 'Kurdish', 'kus': 'Kʋsaal', 'kv': 'Komi',
    'kw': 'Cornish', 'ky': 'Kyrgyz', 'lad': 'Ladino', 'lb': 'Luxembourgish',
    'lbe': 'Lak', 'lez': 'Lezghian', 'lfn': 'Lingua Franca Nova', 'lg': 'Ganda',
    'li': 'Limburgish', 'lij': 'Ligurian', 'lld': 'Ladin', 'lmo': 'Lombard',
    'ln': 'Lingala', 'lo': 'Lao', 'ltg': 'Latgalian', 'lv': 'Latvian',
    'mad': 'Madurese', 'mai': 'Maithili', 'map-bms': 'Banyumasan',
    'mdf': 'Moksha', 'mg': 'Malagasy', 'mhr': 'Eastern Mari', 'mi': 'Māori',
    'min': 'Minangkabau', 'mk': 'Macedonian', 'mn': 'Mongolian', 'mni': 'Manipuri',
    'mnw': 'Mon', 'mos': 'Mossi', 'mrj': 'Western Mari', 'ms': 'Malay',
    'mt': 'Maltese', 'mwl': 'Mirandese', 'myv': 'Erzya', 'mzn': 'Mazanderani',
    'nah': 'Nahuatl', 'nap': 'Neapolitan', 'nds': 'Low German',
    'nds-nl': 'Low Saxon', 'new': 'Newari', 'nia': 'Nias', 'nn': 'Norwegian Nynorsk',
    'nov': 'Novial', 'nqo': "N'Ko", 'nr': 'Southern Ndebele', 'nrm': 'Norman',
    'nso': 'Northern Sotho', 'nup': 'Nupe', 'nv': 'Navajo', 'ny': 'Chichewa',
    'oc': 'Occitan', 'olo': 'Livvi-Karelian', 'om': 'Oromo', 'or': 'Odia',
    'os': 'Ossetian', 'pa': 'Punjabi', 'pag': 'Pangasinan', 'pam': 'Kapampangan',
    'pap': 'Papiamento', 'pcd': 'Picard', 'pcm': 'Nigerian Pidgin',
    'pdc': 'Pennsylvania German', 'pfl': 'Palatine German', 'pi': 'Pali',
    'pms': 'Piedmontese', 'pnb': 'Western Punjabi', 'pnt': 'Pontic Greek',
    'ps': 'Pashto', 'pwn': 'Paiwan', 'qu': 'Quechua', 'rki': 'Arakanese',
    'rm': 'Romansh', 'rmy': 'Romani', 'rn': 'Rundi', 'roa-rup': 'Aromanian',
    'roa-tara': 'Tarantino', 'rsk': 'Pannonian Rusyn', 'rue': 'Rusyn',
    'rw': 'Kinyarwanda', 'sa': 'Sanskrit', 'sah': 'Sakha', 'sat': 'Santali',
    'sc': 'Sardinian', 'scn': 'Sicilian', 'sd': 'Sindhi', 'se': 'Northern Sami',
    'sg': 'Sango', 'shi': 'Tachelhit', 'shn': 'Shan', 'si': 'Sinhala',
    'simple': 'Simple English', 'skr': 'Saraiki', 'sl': 'Slovenian',
    'sm': 'Samoan', 'smn': 'Inari Sami', 'sn': 'Shona', 'so': 'Somali',
    'srn': 'Sranan Tongo', 'ss': 'Swazi', 'st': 'Southern Sotho',
    'stq': 'Saterland Frisian', 'su': 'Sundanese', 'sw': 'Swahili',
    'syl': 'Sylheti', 'szl': 'Silesian', 'szy': 'Sakizaya', 'tay': 'Tayal',
    'tcy': 'Tulu', 'tdd': 'Tai Nuea', 'te': 'Telugu', 'tet': 'Tetum',
    'tg': 'Tajik', 'th': 'Thai', 'ti': 'Tigrinya', 'tig': 'Tigre',
    'tk': 'Turkmen', 'tl': 'Tagalog', 'tly': 'Talysh', 'tn': 'Tswana',
    'to': 'Tongan', 'tok': 'Toki Pona', 'tpi': 'Tok Pisin', 'trv': 'Taroko',
    'ts': 'Tsonga', 'tt': 'Tatar', 'tum': 'Tumbuka', 'tw': 'Twi',
    'ty': 'Tahitian', 'tyv': 'Tuvan', 'udm': 'Udmurt', 'ug': 'Uyghur',
    'ur': 'Urdu', 'uz': 'Uzbek', 've': 'Venda', 'vec': 'Venetian',
    'vep': 'Veps', 'vls': 'West Flemish', 'vo': 'Volapük', 'wa': 'Walloon',
    'war': 'Waray', 'wo': 'Wolof', 'wuu': 'Wu Chinese', 'xal': 'Kalmyk',
    'xh': 'Xhosa', 'xmf': 'Mingrelian', 'yi': 'Yiddish', 'yo': 'Yoruba',
    'za': 'Zhuang', 'zea': 'Zeelandic', 'zgh': 'Standard Moroccan Tamazight',
    'zh-classical': 'Classical Chinese', 'zh-yue': 'Cantonese', 'zu': 'Zulu'
}

def get_wikipedia_peaks():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get Wikipedia projects with peak counts
        cursor.execute('''
            SELECT 
                SUBSTRING_INDEX(project, '.', 1) as lang_code,
                COUNT(*) as peak_count
            FROM editor_alerts 
            WHERE project LIKE '%wikipedia%'
            GROUP BY lang_code
            ORDER BY peak_count DESC
        ''')
        results = cursor.fetchall()
        
        print(f"\n{'Language':<35} {'Code':<15} {'Peaks':>8}")
        print("=" * 60)
        
        for lang_code, peak_count in results:
            lang_name = LANGUAGE_NAMES.get(lang_code, f'Unknown ({lang_code})')
            print(f"{lang_name:<35} {lang_code:<15} {peak_count:>8}")
        
        print(f"\nTotal: {len(results)} Wikipedia language editions with editor count peaks")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    get_wikipedia_peaks()
