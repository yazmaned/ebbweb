import re
from django.core.management.base import BaseCommand
from content.models import Material


class Command(BaseCommand):
    help = (
        "Converts any Material with material_type='vimeo' whose embed_url is still "
        "a plain vimeo.com share link (e.g. vimeo.com/123456789) into the real "
        "embeddable player.vimeo.com/video/123456789 URL — same regex the admin "
        "explorer's '+ Vimeo Ekle' button already uses for new entries, applied "
        "retroactively to ones added before that conversion existed."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without actually saving anything.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        videos = Material.objects.filter(material_type='vimeo')

        fixed = 0
        already_ok = 0
        unmatched = 0

        for material in videos:
            url = material.embed_url or ''

            if 'player.vimeo.com' in url:
                already_ok += 1
                continue

            match = re.search(r'vimeo\.com/(?:video/)?(\d+)', url)
            if not match:
                unmatched += 1
                self.stdout.write(self.style.WARNING(
                    f'  Could not parse video ID — "{material.title}" (pk={material.pk}): {url}'
                ))
                continue

            video_id = match.group(1)
            new_url = f'https://player.vimeo.com/video/{video_id}'

            self.stdout.write(f'  "{material.title}" (pk={material.pk}): {url}  ->  {new_url}')

            if not dry_run:
                material.embed_url = new_url
                material.save(update_fields=['embed_url'])

            fixed += 1

        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'DRY RUN — would fix {fixed}, already correct: {already_ok}, unparseable: {unmatched}'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Fixed {fixed}, already correct: {already_ok}, unparseable: {unmatched}'
            ))