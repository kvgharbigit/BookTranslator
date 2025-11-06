// Language-specific upload messages for all supported languages
// Each language has fun, culturally-relevant messages for the upload flow

export interface LanguageMessages {
  start: string[];
  progress: string[];
  analyzing: string[];
}

export const UPLOAD_MESSAGES: Record<string, LanguageMessages> = {
  'en': {
    start: ['📚 Welcome! Opening your book...', '✨ Preparing your English journey...', '🎭 Let\'s begin the magic...'],
    progress: ['📤 Uploading to the cloud...', '📚 English brilliance loading...', '✨ Almost there...'],
    analyzing: ['🔍 Counting words...', '🧮 Calculating estimate...', '💰 Price coming up...']
  },
  'es': {
    start: ['📚 ¡Bienvenido! Opening your libro...', '✨ Preparando tu Spanish journey...', '🌮 ¡Vámonos! Let\'s begin...'],
    progress: ['📤 Uploading to la nube...', '📚 Spanish magic loading...', '✨ Casi terminado...'],
    analyzing: ['🔍 Contando palabras...', '🧮 Calculating precio...', '💰 Spanish estimate coming...']
  },
  'fr': {
    start: ['📚 Bonjour! Opening your livre...', '✨ Preparing your French voyage...', '🥐 Allons-y! Let\'s begin...'],
    progress: ['📤 Uploading to le cloud...', '📚 French elegance loading...', '✨ Presque fini...'],
    analyzing: ['🔍 Counting les mots...', '🧮 Calculating le prix...', '💰 French estimate arriving...']
  },
  'de': {
    start: ['📚 Guten Tag! Opening your Buch...', '✨ Preparing your German Reise...', '🍺 Los geht\'s! Let\'s begin...'],
    progress: ['📤 Uploading to die Cloud...', '📚 German precision loading...', '✨ Fast fertig...'],
    analyzing: ['🔍 Counting die Wörter...', '🧮 Calculating der Preis...', '💰 German estimate ready...']
  },
  'zh': {
    start: ['📚 你好! Opening your 书...', '✨ Preparing your Chinese 旅程...', '🏮 走吧! Let\'s begin...'],
    progress: ['📤 Uploading to 云端...', '📚 Chinese wisdom loading...', '✨ 快好了...'],
    analyzing: ['🔍 Counting 字数...', '🧮 Calculating 价格...', '💰 Chinese estimate 准备中...']
  },
  'ja': {
    start: ['📚 こんにちは! Opening your 本...', '✨ Preparing your Japanese 旅...', '🍜 行きましょう! Let\'s begin...'],
    progress: ['📤 Uploading to クラウド...', '📚 Japanese harmony loading...', '✨ もうすぐ...'],
    analyzing: ['🔍 Counting 言葉...', '🧮 Calculating 価格...', '💰 Japanese estimate 準備中...']
  },
  'pt': {
    start: ['📚 Olá! Opening your livro...', '✨ Preparing your Portuguese jornada...', '⚽ Vamos! Let\'s begin...'],
    progress: ['📤 Uploading to a nuvem...', '📚 Portuguese soul loading...', '✨ Quase pronto...'],
    analyzing: ['🔍 Counting as palavras...', '🧮 Calculating o preço...', '💰 Portuguese estimate ready...']
  },
  'ru': {
    start: ['📚 Привет! Opening your книга...', '✨ Preparing your Russian путь...', '❄️ Поехали! Let\'s begin...'],
    progress: ['📤 Uploading to облако...', '📚 Russian grandeur loading...', '✨ Почти готово...'],
    analyzing: ['🔍 Counting слова...', '🧮 Calculating цена...', '💰 Russian estimate готов...']
  },
  'ar': {
    start: ['📚 السلام عليكم! Opening your كتاب...', '✨ Preparing your Arabic رحلة...', '🕌 يلا! Let\'s begin...'],
    progress: ['📤 Uploading to السحابة...', '📚 Arabic beauty loading...', '✨ تقريبا جاهز...'],
    analyzing: ['🔍 Counting كلمات...', '🧮 Calculating السعر...', '💰 Arabic estimate جاهز...']
  },
  'bn': {
    start: ['📚 নমস্কার! Opening your বই...', '✨ Preparing your Bengali যাত্রা...', '🎭 চলুন! Let\'s begin...'],
    progress: ['📤 Uploading to ক্লাউড...', '📚 Bengali beauty loading...', '✨ প্রায় প্রস্তুত...'],
    analyzing: ['🔍 Counting শব্দ...', '🧮 Calculating দাম...', '💰 Bengali estimate প্রস্তুত...']
  },
  'bg': {
    start: ['📚 Здравей! Opening your книга...', '✨ Preparing your Bulgarian пътуване...', '🌹 Хайде! Let\'s begin...'],
    progress: ['📤 Uploading to облак...', '📚 Bulgarian beauty loading...', '✨ Почти готово...'],
    analyzing: ['🔍 Counting думи...', '🧮 Calculating цена...', '💰 Bulgarian estimate готов...']
  },
  'ca': {
    start: ['📚 Hola! Opening your llibre...', '✨ Preparing your Catalan viatge...', '🏴 Anem! Let\'s begin...'],
    progress: ['📤 Uploading to el núvol...', '📚 Catalan pride loading...', '✨ Gairebé a punt...'],
    analyzing: ['🔍 Counting paraules...', '🧮 Calculating preu...', '💰 Catalan estimate llest...']
  },
  'hr': {
    start: ['📚 Bok! Opening your knjiga...', '✨ Preparing your Croatian putovanje...', '🌊 Idemo! Let\'s begin...'],
    progress: ['📤 Uploading to oblak...', '📚 Croatian beauty loading...', '✨ Skoro gotovo...'],
    analyzing: ['🔍 Counting riječi...', '🧮 Calculating cijena...', '💰 Croatian estimate spreman...']
  },
  'cs': {
    start: ['📚 Ahoj! Opening your kniha...', '✨ Preparing your Czech cesta...', '🍺 Pojďme! Let\'s begin...'],
    progress: ['📤 Uploading to cloud...', '📚 Czech magic loading...', '✨ Skoro hotovo...'],
    analyzing: ['🔍 Counting slova...', '🧮 Calculating cena...', '💰 Czech estimate připraven...']
  },
  'da': {
    start: ['📚 Hej! Opening your bog...', '✨ Preparing your Danish rejse...', '🧁 Lad os gå! Let\'s begin...'],
    progress: ['📤 Uploading to skyen...', '📚 Danish hygge loading...', '✨ Næsten færdig...'],
    analyzing: ['🔍 Counting ord...', '🧮 Calculating pris...', '💰 Danish estimate klar...']
  },
  'nl': {
    start: ['📚 Hallo! Opening your boek...', '✨ Preparing your Dutch reis...', '🌷 Laten we gaan! Let\'s begin...'],
    progress: ['📤 Uploading to de cloud...', '📚 Dutch directness loading...', '✨ Bijna klaar...'],
    analyzing: ['🔍 Counting woorden...', '🧮 Calculating prijs...', '💰 Dutch estimate gereed...']
  },
  'et': {
    start: ['📚 Tere! Opening your raamat...', '✨ Preparing your Estonian teekond...', '🌲 Lähme! Let\'s begin...'],
    progress: ['📤 Uploading to pilv...', '📚 Estonian precision loading...', '✨ Peaaegu valmis...'],
    analyzing: ['🔍 Counting sõnad...', '🧮 Calculating hind...', '💰 Estonian estimate valmis...']
  },
  'fi': {
    start: ['📚 Hei! Opening your kirja...', '✨ Preparing your Finnish matka...', '🧖 Mennään! Let\'s begin...'],
    progress: ['📤 Uploading to pilvi...', '📚 Finnish sisu loading...', '✨ Melkein valmis...'],
    analyzing: ['🔍 Counting sanat...', '🧮 Calculating hinta...', '💰 Finnish estimate valmis...']
  },
  'el': {
    start: ['📚 Γεια σου! Opening your βιβλίο...', '✨ Preparing your Greek ταξίδι...', '🏛️ Πάμε! Let\'s begin...'],
    progress: ['📤 Uploading to σύννεφο...', '📚 Greek wisdom loading...', '✨ Σχεδόν έτοιμο...'],
    analyzing: ['🔍 Counting λέξεις...', '🧮 Calculating τιμή...', '💰 Greek estimate έτοιμο...']
  },
  'he': {
    start: ['📚 שלום! Opening your ספר...', '✨ Preparing your Hebrew מסע...', '✡️ בוא נתחיל! Let\'s begin...'],
    progress: ['📤 Uploading to ענן...', '📚 Hebrew beauty loading...', '✨ כמעט מוכן...'],
    analyzing: ['🔍 Counting מילים...', '🧮 Calculating מחיר...', '💰 Hebrew estimate מוכן...']
  },
  'hi': {
    start: ['📚 नमस्ते! Opening your पुस्तक...', '✨ Preparing your Hindi यात्रा...', '🪔 चलो! Let\'s begin...'],
    progress: ['📤 Uploading to क्लाउड...', '📚 Hindi magic loading...', '✨ लगभग तैयार...'],
    analyzing: ['🔍 Counting शब्द...', '🧮 Calculating कीमत...', '💰 Hindi estimate तैयार...']
  },
  'hu': {
    start: ['📚 Szia! Opening your könyv...', '✨ Preparing your Hungarian utazás...', '🌶️ Gyerünk! Let\'s begin...'],
    progress: ['📤 Uploading to felhő...', '📚 Hungarian spirit loading...', '✨ Majdnem kész...'],
    analyzing: ['🔍 Counting szavak...', '🧮 Calculating ár...', '💰 Hungarian estimate kész...']
  },
  'id': {
    start: ['📚 Halo! Opening your buku...', '✨ Preparing your Indonesian perjalanan...', '🏝️ Ayo! Let\'s begin...'],
    progress: ['📤 Uploading to awan...', '📚 Indonesian beauty loading...', '✨ Hampir selesai...'],
    analyzing: ['🔍 Counting kata...', '🧮 Calculating harga...', '💰 Indonesian estimate siap...']
  },
  'it': {
    start: ['📚 Ciao! Opening your libro...', '✨ Preparing your Italian viaggio...', '🍝 Andiamo! Let\'s begin...'],
    progress: ['📤 Uploading to la nuvola...', '📚 Italian artistry loading...', '✨ Quasi finito...'],
    analyzing: ['🔍 Counting le parole...', '🧮 Calculating il prezzo...', '💰 Italian estimate coming...']
  },
  'ko': {
    start: ['📚 안녕! Opening your 책...', '✨ Preparing your Korean 여행...', '🎤 가자! Let\'s begin...'],
    progress: ['📤 Uploading to 클라우드...', '📚 Korean flow loading...', '✨ 거의 다...'],
    analyzing: ['🔍 Counting 단어...', '🧮 Calculating 가격...', '💰 Korean estimate 준비중...']
  },
  'lv': {
    start: ['📚 Sveiki! Opening your grāmata...', '✨ Preparing your Latvian ceļojums...', '🌲 Ejam! Let\'s begin...'],
    progress: ['📤 Uploading to mākonis...', '📚 Latvian beauty loading...', '✨ Gandrīz gatavs...'],
    analyzing: ['🔍 Counting vārdi...', '🧮 Calculating cena...', '💰 Latvian estimate gatavs...']
  },
  'lt': {
    start: ['📚 Labas! Opening your knyga...', '✨ Preparing your Lithuanian kelionė...', '🏰 Einam! Let\'s begin...'],
    progress: ['📤 Uploading to debesis...', '📚 Lithuanian charm loading...', '✨ Beveik baigta...'],
    analyzing: ['🔍 Counting žodžiai...', '🧮 Calculating kaina...', '💰 Lithuanian estimate paruošta...']
  },
  'ms': {
    start: ['📚 Hello! Opening your buku...', '✨ Preparing your Malay perjalanan...', '🌺 Jom! Let\'s begin...'],
    progress: ['📤 Uploading to awan...', '📚 Malay beauty loading...', '✨ Hampir siap...'],
    analyzing: ['🔍 Counting perkataan...', '🧮 Calculating harga...', '💰 Malay estimate sedia...']
  },
  'no': {
    start: ['📚 Hei! Opening your bok...', '✨ Preparing your Norwegian reise...', '⛷️ La oss gå! Let\'s begin...'],
    progress: ['📤 Uploading to skyen...', '📚 Norwegian charm loading...', '✨ Nesten ferdig...'],
    analyzing: ['🔍 Counting ord...', '🧮 Calculating pris...', '💰 Norwegian estimate klar...']
  },
  'fa': {
    start: ['📚 سلام! Opening your کتاب...', '✨ Preparing your Persian سفر...', '🌹 بریم! Let\'s begin...'],
    progress: ['📤 Uploading to ابر...', '📚 Persian poetry loading...', '✨ تقریبا آماده...'],
    analyzing: ['🔍 Counting کلمات...', '🧮 Calculating قیمت...', '💰 Persian estimate آماده...']
  },
  'pl': {
    start: ['📚 Cześć! Opening your książka...', '✨ Preparing your Polish podróż...', '🥟 Chodźmy! Let\'s begin...'],
    progress: ['📤 Uploading to chmura...', '📚 Polish spirit loading...', '✨ Prawie gotowe...'],
    analyzing: ['🔍 Counting słowa...', '🧮 Calculating cena...', '💰 Polish estimate gotowy...']
  },
  'ro': {
    start: ['📚 Bună! Opening your carte...', '✨ Preparing your Romanian călătorie...', '🏰 Hai să mergem! Let\'s begin...'],
    progress: ['📤 Uploading to norul...', '📚 Romanian beauty loading...', '✨ Aproape gata...'],
    analyzing: ['🔍 Counting cuvinte...', '🧮 Calculating preț...', '💰 Romanian estimate gata...']
  },
  'sr': {
    start: ['📚 Здраво! Opening your књига...', '✨ Preparing your Serbian путовање...', '🎭 Хајде! Let\'s begin...'],
    progress: ['📤 Uploading to облак...', '📚 Serbian soul loading...', '✨ Скоро готово...'],
    analyzing: ['🔍 Counting речи...', '🧮 Calculating цена...', '💰 Serbian estimate спреман...']
  },
  'sk': {
    start: ['📚 Ahoj! Opening your kniha...', '✨ Preparing your Slovak cesta...', '⛰️ Poďme! Let\'s begin...'],
    progress: ['📤 Uploading to cloud...', '📚 Slovak charm loading...', '✨ Takmer hotovo...'],
    analyzing: ['🔍 Counting slová...', '🧮 Calculating cena...', '💰 Slovak estimate pripravený...']
  },
  'sl': {
    start: ['📚 Živjo! Opening your knjiga...', '✨ Preparing your Slovenian potovanje...', '🏔️ Gremo! Let\'s begin...'],
    progress: ['📤 Uploading to oblak...', '📚 Slovenian charm loading...', '✨ Skoraj končano...'],
    analyzing: ['🔍 Counting besede...', '🧮 Calculating cena...', '💰 Slovenian estimate pripravljen...']
  },
  'sv': {
    start: ['📚 Hej! Opening your bok...', '✨ Preparing your Swedish resa...', '☕ Vi kör! Let\'s begin...'],
    progress: ['📤 Uploading to molnet...', '📚 Swedish hygge loading...', '✨ Nästan klar...'],
    analyzing: ['🔍 Counting ord...', '🧮 Calculating pris...', '💰 Swedish estimate redo...']
  },
  'ta': {
    start: ['📚 வணக்கம்! Opening your புத்தகம்...', '✨ Preparing your Tamil பயணம்...', '🎭 போகலாம்! Let\'s begin...'],
    progress: ['📤 Uploading to கிளவுட்...', '📚 Tamil heritage loading...', '✨ கிட்டத்தட்ட தயார்...'],
    analyzing: ['🔍 Counting வார்த்தைகள்...', '🧮 Calculating விலை...', '💰 Tamil estimate தயார்...']
  },
  'te': {
    start: ['📚 నమస్కారం! Opening your పుస్తకం...', '✨ Preparing your Telugu ప్రయాణం...', '🌺 వెళ్దాం! Let\'s begin...'],
    progress: ['📤 Uploading to క్లౌడ్...', '📚 Telugu elegance loading...', '✨ దాదాపు సిద్ధంగా...'],
    analyzing: ['🔍 Counting పదాలు...', '🧮 Calculating ధర...', '💰 Telugu estimate సిద్ధం...']
  },
  'th': {
    start: ['📚 สวัสดี! Opening your หนังสือ...', '✨ Preparing your Thai การเดินทาง...', '🐘 ไปกันเถอะ! Let\'s begin...'],
    progress: ['📤 Uploading to คลาวด์...', '📚 Thai grace loading...', '✨ เกือบเสร็จแล้ว...'],
    analyzing: ['🔍 Counting คำ...', '🧮 Calculating ราคา...', '💰 Thai estimate พร้อม...']
  },
  'tr': {
    start: ['📚 Merhaba! Opening your kitap...', '✨ Preparing your Turkish yolculuk...', '☕ Hadi gidelim! Let\'s begin...'],
    progress: ['📤 Uploading to bulut...', '📚 Turkish delight loading...', '✨ Neredeyse tamam...'],
    analyzing: ['🔍 Counting kelimeler...', '🧮 Calculating fiyat...', '💰 Turkish estimate hazır...']
  },
  'ur': {
    start: ['📚 السلام علیکم! Opening your کتاب...', '✨ Preparing your Urdu سفر...', '📜 چلیں! Let\'s begin...'],
    progress: ['📤 Uploading to کلاؤڈ...', '📚 Urdu poetry loading...', '✨ تقریباً تیار...'],
    analyzing: ['🔍 Counting الفاظ...', '🧮 Calculating قیمت...', '💰 Urdu estimate تیار...']
  },
  'vi': {
    start: ['📚 Xin chào! Opening your sách...', '✨ Preparing your Vietnamese hành trình...', '🍜 Đi thôi! Let\'s begin...'],
    progress: ['📤 Uploading to đám mây...', '📚 Vietnamese flow loading...', '✨ Sắp xong...'],
    analyzing: ['🔍 Counting từ...', '🧮 Calculating giá...', '💰 Vietnamese estimate sẵn sàng...']
  }
};

export function getLanguageUploadMessages(langCode: string, langName: string): LanguageMessages {
  return UPLOAD_MESSAGES[langCode] || {
    start: [`📚 Opening your book for ${langName}...`, `✨ Preparing your ${langName} journey...`],
    progress: [`📤 Uploading for ${langName}...`, `📚 ${langName} magic loading...`, `✨ Almost there...`],
    analyzing: [`🔍 Analyzing for ${langName}...`, `🧮 Calculating ${langName} estimate...`]
  };
}
