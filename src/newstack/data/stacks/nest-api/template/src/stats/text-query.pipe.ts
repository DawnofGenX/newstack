import {
  BadRequestException,
  Injectable,
  PipeTransform,
} from "@nestjs/common";

/**
 * Hand-rolled validation for the `text` query parameter: it must be present.
 * No class-validator: the stack ships no extra runtime dependencies.
 */
@Injectable()
export class TextQueryPipe implements PipeTransform<unknown, string> {
  transform(value: unknown): string {
    if (typeof value !== "string") {
      throw new BadRequestException("text is required");
    }
    return value;
  }
}
