# video-uploads

מאגר לסרטונים שמהם Claude חותך קליפים ויראליים ל-YouTube Shorts.

**איך מוסיפים סרטון חדש:**
1. נכנסים ל-https://github.com/refarafaraful-code/video-uploads/releases/new
2. Choose a tag ← שם חדש (v3, v4...) ← Create new tag
3. מעלים את הסרטון ב-Attach binaries (עד 2GB) ← Publish release (או Save draft)
4. כותבים ל-Claude: "העליתי סרטון חדש"

Claude יבדוק שהסרטון לא עובד כבר, יוריד, יתמלל, יבחר את כל הרגעים החזקים (בלי מכסה), יערוך קליפים עם כתוביות, אפקטים וסאונד,
ויתזמן אותם ב-Metricool לפרסום ב-YouTube (15:00 שעון ניו יורק, קליף ביום).

- `clipper/` – כלי העריכה (תמלול, אפקטים קוליים, עריכה)
- `projects/` – התמלולים וההגדרות של כל סרטון שנערך
- `shorts-*/` – הקליפים המוכנים שמתפרסמים
- `production_data/` – ההוראות הקבועות (CLIPPINGMASTER), רישום ההפקות (מונע כפילויות) ויומן
