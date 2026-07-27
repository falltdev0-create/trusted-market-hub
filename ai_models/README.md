# AI models data and weights

هذا المجلد يحتوي على بنية البيانات والوزن الخاصة بنماذج الذكاء الاصطناعي.

- condition_model/weights/: أوزان نموذج تقييم الحالة (model.pt).
- document_model/weights/: أوزان نموذج مطابقة الوثائق (model.pt).
- pricing_model/weights/: نموذج تقدير السعر المحفوظ (model.pkl).
- condition_model/dataset/: بيانات التدريب للتصنيف.

التنسيق المتوقع لبيانات التدريب:

`
ai_models/condition_model/dataset/
  train/
    poor/
    good/
    excellent/
  val/
    poor/
    good/
    excellent/
`

ضع بيانات الصور في هذه المجلدات ثم درِّب النموذج باستخدام python predictor.py --dataset ./dataset --save ./weights/model.pt داخل i_models/condition_model/.
