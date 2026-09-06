set -e
mkdir -p img/dresser img/chest
i=0
for u in $(grep "goods/28643/slideimages" dresser_walnut_sq_imgs.txt | sed 's/?d=.*//' | sort -u); do
  i=$((i+1)); curl -s -A "Mozilla/5.0" -o "img/dresser/$(printf %02d $i).jpg" "$u"; echo "$i $u" >> img/dresser/_src.txt
done
i=0
for u in $(grep "goods/22580/slideimages" chest_walnut_high_imgs.txt | sed 's/?d=.*//' | sort -u); do
  i=$((i+1)); curl -s -A "Mozilla/5.0" -o "img/chest/$(printf %02d $i).jpg" "$u"; echo "$i $u" >> img/chest/_src.txt
done
