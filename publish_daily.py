import argparse
from publisher import publish

p=argparse.ArgumentParser(description='Publish the next scheduled Smart Learning Lab content item.')
p.add_argument('--content-type',default='auto',help='Use auto or one of the 15 content types.')
p.add_argument('--index',type=int,help='Override the next index for the selected content type.')
p.add_argument('--schedule-cron',default='',help='Exact GitHub schedule expression, used to keep delayed scheduled runs mapped to the intended format.')
a=p.parse_args()
publish(a.content_type,a.index,do_facebook=True,do_instagram=True,schedule_cron=a.schedule_cron)
